import sys
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
        self.heos_control = self.get_entity("input_boolean.heos_is_being_setup")
        self.heos_ungroup = self.get_entity("input_boolean.heos_ungrouped")
        self.heos_group = self.get_entity("input_boolean.heos_grouped")
        self.log("Done initializing")

    async def ungroup(self, entity, attribute, old, new, kwargs):
        heos_controlled = await self.heos_control.is_state("on")
        heos_ungrouped = await self.heos_ungroup.is_state("on")
        if not (heos_controlled or heos_ungrouped):
            self.heos_control.call_service("turn_on")

            heos = Heos("192.168.179.193")

            await heos.connect(auto_reconnect=True)
            players = await heos.get_players(refresh=True)
            self.log(f"keys are now: {players.keys()}")
            heos_left, heos_right = None, None
            for k in players.keys():
                if len(re.findall("right", str(players[k]))) > 0:
                    heos_right = players[k]
                    await heos_right.stop()
                    await heos_right.play_input("inputs/aux_in_1")
                    await heos_right.play()
            await heos.disconnect()

            response = sh.shoe("-H", "192.168.179.193", "-c", "GetGroupUUID")
            # self.log(response)
            matches = re.findall(r":\s.*", response)

            if matches:
                groupUUID = matches[-1][2:]
                # self.log(f"groupUUID is {groupUUID}")

                #  First stop playback if playing
                # sh.shoe("-H", "192.168.179.193", "-c", "Stop")
                # self.log(f"Stop response right is {response}")
                # sh.shoe("-H", "192.168.179.178", "-c", "Stop")
                # self.log(f"Stop response left is {response}")

                sh.shoe(
                    "-H",
                    "192.168.179.193",
                    "-c",
                    "DestroyGroup",
                    "-a",
                    "GroupUUID",
                    groupUUID,
                )
                # self.log(f"Destroy response is {response}")

            # # self.call_service(
            # #     "media_player/select_source",
            # #     source="Denon Home right rear - AUX In",
            # #     entity_id=[
            # #         "media_player.denon_home_right_rear",
            # #     ],
            # # )

            # # self.call_service(
            # #     "media_player/volume_set",
            # #     entity_id="media_player.denon_home_right_rear",
            # #     volume_level=0.66,
            # # )

            # response = sh.shoe("-H", "192.168.179.193", "-c", "Play")
            # self.log(f"Play response right is {response}")

            # Let's try to just control the Heos devices via pyheos
            heos = Heos("192.168.179.193")

            await heos.connect(auto_reconnect=True)
            players = await heos.get_players(refresh=True)
            self.log(players.keys())
            heos_left, heos_right = None, None
            for k in players.keys():
                if len(re.findall("right", str(players[k]))) > 0:
                    heos_right = players[k]
                    await heos_right.play_input("inputs/aux_in_1")
                    await heos_right.set_volume(66)
                    await heos_right.play()
                elif len(re.findall("left", str(players[k]))) > 0:
                    self.log("Calling left")
                    heos_left = players[k]
                    await heos_left.play_input("inputs/aux_in_1")
                    await heos_left.set_volume(66)
                    await heos_left.play()

            await heos.disconnect()

            await heos.connect(auto_reconnect=True)
            new_players = await heos.get_players(refresh=True)
            for k in new_players.keys():
                if len(re.findall("left", str(new_players[k]))) > 0:
                    self.log("Calling left second time")
                    heos_left = new_players[k]
                    await heos_left.play()
                    await heos_left.play_input("inputs/aux_in_1")
    
            await heos.disconnect()
            response = sh.shoe("-H", "192.168.179.178", "-c", "Play")

            self.heos_control.call_service("turn_off")
            self.heos_ungroup.call_service("turn_on")
            self.heos_group.call_service("turn_off")
            self.call_service("notify/mobile_app_pixel_5", title="HEOS 5.1", message="Heos is in 5.1 mode")
            self.call_service("notify/lg_webos_tv_oled55g1rla", title="HEOS 5.1", message="Heos is in 5.1 mode")

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
            # self.log(f"Stop response right is {response}")
            response = sh.shoe("-H", "192.168.179.178", "-c", "Stop")
            # self.log(f"Stop response left is {response}")

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
            # self.log(response)

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
            # self.log(response)

            self.call_service(
                "input_boolean/turn_off", entity_id="input_boolean.heos_is_being_setup"
            )

            self.call_service(
                "input_boolean/turn_on", entity_id="input_boolean.heos_grouped"
            )

            self.call_service(
                "input_boolean/turn_off", entity_id="input_boolean.heos_ungrouped"
            )
