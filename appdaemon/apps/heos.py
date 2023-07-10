import re
import appdaemon.plugins.hass.hassapi as hass
import sh
from pyheos import Heos


class ControlHeos(hass.Hass):
    def initialize(self):
        self.log("Initializing heos app")
        self.listen_state(
            self.ungroup, "media_player.lg_webos_tv_oled55g1rla", new="on"
        )
        self.listen_state(self.ungroup, "input_button.heos_ungroup")
        self.listen_state(self.group, "media_player.lg_webos_tv_oled55g1rla", new="off")
        self.listen_state(self.group, "input_button.heos_group")
        self.log("Done initializing")

    async def ungroup(self, entity, attribute, old, new, kwargs):
        heos_control = self.get_entity("input_boolean.heos_is_being_setup")
        heos_controlled = await heos_control.is_state("on")
        heos_ungroup = self.get_entity("input_boolean.heos_ungrouped")
        heos_ungrouped = await heos_ungroup.is_state("on")
        if not (heos_controlled or heos_ungrouped):
            self.call_service(
                "input_boolean/turn_on", entity_id="input_boolean.heos_is_being_setup"
            )

            response = sh.shoe("-H", "192.168.179.193", "-c", "GetGroupUUID")
            self.log(response)
            matches = re.findall(r":\s.*", response)

            if matches:
                groupUUID = matches[-1][2:]
                self.log(f"groupUUID is {groupUUID}")

                #  First stop playback if playing
                response = sh.shoe("-H", "192.168.179.193", "-c", "Stop")
                self.log(f"Stop response right is {response}")
                response = sh.shoe("-H", "192.168.179.178", "-c", "Stop")
                self.log(f"Stop response left is {response}")

                response = sh.shoe(
                    "-H",
                    "192.168.179.193",
                    "-c",
                    "DestroyGroup",
                    "-a",
                    "GroupUUID",
                    groupUUID,
                )
                self.log(f"Destroy response is {response}")

            self.call_service(
                "media_player/select_source",
                source="Denon Home right rear - AUX In",
                entity_id=[
                    "media_player.denon_home_right_rear",
                ],
            )

            self.call_service(
                "media_player/volume_set",
                entity_id="media_player.denon_home_right_rear",
                volume_level=0.66,
            )

            response = sh.shoe("-H", "192.168.179.193", "-c", "Play")
            self.log(f"Play response right is {response}")

            # This Heos device probably is not available after the unjoining so
            # let's call it from pyheos (maybe later by reloading integration)
            heos = Heos("192.168.179.193")

            await heos.connect(auto_reconnect=True)
            players = await heos.get_players(refresh=True)

            heos_left = players[751373395]
            await heos_left.play_input("inputs/aux_in_1")
            await heos_left.set_volume(66)
            await heos.disconnect()

            self.call_service(
                "input_boolean/turn_off", entity_id="input_boolean.heos_is_being_setup"
            )
            self.call_service(
                "input_boolean/turn_on", entity_id="input_boolean.heos_ungrouped"
            )
            self.call_service(
                "input_boolean/turn_off", entity_id="input_boolean.heos_grouped"
            )

    def group(self, entity, attribute, old, new, kwargs):
        heos_control = self.get_entity("input_boolean.heos_is_being_setup")
        heos_controlled = heos_control.is_state("on")
        heos_group = self.get_entity("input_boolean.heos_grouped")
        heos_grouped = heos_group.is_state("on")
        if not (heos_controlled or heos_grouped):
            self.call_service(
                "input_boolean/turn_on", entity_id="input_boolean.heos_is_being_setup"
            )

            self.call_service(
                "media_player/volume_set",
                entity_id="media_player.denon_home_right_rear",
                volume_level=0.2,
            )

            self.call_service(
                "media_player/volume_set",
                entity_id="media_player.denon_home_left_rear",
                volume_level=0.2,
            )

            #  First stop playback if playing
            response = sh.shoe("-H", "192.168.179.193", "-c", "Stop")
            self.log(f"Stop response right is {response}")
            response = sh.shoe("-H", "192.168.179.178", "-c", "Stop")
            self.log(f"Stop response left is {response}")

            response = sh.shoe(
                "-H",
                "192.168.179.193",
                "-c",
                "CreateZone",
                "-a",
                "ZoneFriendlyName",
                "Danger Zone",
                "-a",
                "ZoneIPList",
                "192.168.179.178",
            )
            self.log(response)

            response = sh.shoe(
                "-H",
                "192.168.179.193",
                "-c",
                "CreateGroup",
                "-a",
                "GroupFriendlyName",
                "Stereo Friends",
                "-a",
                "GroupMemberUUIDList",
                "11b9df62864e1a53008000a96f10e920,6bcb52d849471444008000a96f107e22",
            )
            self.log(response)

            self.call_service(
                "input_boolean/turn_off", entity_id="input_boolean.heos_is_being_setup"
            )

            self.call_service(
                "input_boolean/turn_on", entity_id="input_boolean.heos_grouped"
            )

            self.call_service(
                "input_boolean/turn_off", entity_id="input_boolean.heos_ungrouped"
            )
