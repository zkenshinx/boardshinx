import zipfile
import json
from src import game as game_module

class GameStateManager:

    @staticmethod
    def save_game_state(game, output_zip_path="game_state.zip"):
        zipf = zipfile.ZipFile(output_zip_path, "w")
        game_state = []
        for sprite in game.sprite_group.sprites():
            if sprite._type == "image":
                game_state.append({
                    "type": "image",
                    "id": sprite._id,
                    "x": sprite.world_rect.x,
                    "y": sprite.world_rect.y,
                    "width": sprite.world_rect.width,
                    "height": sprite.world_rect.height,
                    "front_path": sprite.front_image_path,
                    "z_index": sprite.z_index,
                    "render": sprite.render,
                    "flipable": sprite.flipable,
                    "draggable": sprite.draggable,
                    "rotatable": sprite.rotatable,
                    "rotation": sprite.rotation,
                    "is_front": sprite.is_front,
                })
                if sprite.flipable:
                    game_state[-1]["back_path"] = sprite.back_image_path
                    zipf.write(sprite.back_image_path, sprite.back_image_path)
                zipf.write(sprite.front_image_path, sprite.front_image_path)
        for sprite in game.sprite_group.sprites():
            if sprite._type == "holder":
                game_state.append({
                    "type": "holder",
                    "id": sprite._id,
                    "x": sprite.world_rect.x,
                    "y": sprite.world_rect.y,
                    "width": sprite.world_rect.width,
                    "height": sprite.world_rect.height,
                    "z_index": sprite.z_index,
                    "deck": [f._id for f in sprite.deck]
                })
            elif sprite._type == "player_hand":
                game_state.append({
                    "type": "player_hand",
                    "id": sprite._id,
                    "x": sprite.world_rect.x,
                    "y": sprite.world_rect.y,
                    "width": sprite.world_rect.width,
                    "height": sprite.world_rect.height
                })
        for sprite in game.sprite_group.sprites():
            if "button" in sprite._type:
                arr = {
                    "type": sprite._type,
                    "id": sprite._id,
                    "x": sprite.world_rect.x,
                    "y": sprite.world_rect.y,
                    "width": sprite.world_rect.width,
                    "height": sprite.world_rect.height,
                    "z_index": sprite.z_index,
                }
                if sprite._type == "retrieve_button":
                    arr["holder"] = sprite.deck._id
                    arr["images_to_retrieve"] = [f._id for f in sprite.images_to_retrieve]
                elif sprite._type == "shuffle_button":
                    arr["holder"] = sprite.holder._id
                game_state.append(arr)
        for sprite in game.sprite_group.sprites():
            if sprite._type == "dice":
                game_state.append({
                    "type": "dice",
                    "id": sprite._id,
                    "x": sprite.world_rect.x,
                    "y": sprite.world_rect.y,
                    "width": sprite.world_rect.width,
                    "height": sprite.world_rect.height,
                    "z_index": sprite.z_index,
                    "paths": sprite.paths,
                    "draggable": sprite.draggable,
                    "rotatable": sprite.rotatable,
                    "rotation": sprite.rotation,
                })
                for p in sprite.paths:
                    zipf.write(p, p)
        zipf.writestr("game_state.json", json.dumps(game_state, indent=2))

    @staticmethod
    def load_game_state(game, input_zip_path="game_state.zip"):
        zipf = zipfile.ZipFile(input_zip_path, "r")
        # zipf.extractall()
        with open("game_state.json", 'r') as file:
            game_state = json.load(file)
        for sprite in game_state:
            if sprite["type"] == "image":
                if sprite["flipable"]:
                    image = game_module.Image(sprite["front_path"], sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.sprite_group, game, flipable=True, back_path=sprite["back_path"])
                else:
                    image = game_module.Image(sprite["front_path"], sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.sprite_group, game)
                image.z_index = sprite["z_index"]
                image.render = sprite["render"]
                image._id = sprite["id"]
                image.draggable = sprite["draggable"]
                image.rotatable = sprite["rotatable"]
                image.rotation = sprite["rotation"]
                image.is_front = sprite["is_front"]
                game.mp[image._id] = image
                image.update()
        for sprite in game_state:
            if sprite["type"] == "holder":
                holder = game_module.Holder(sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.sprite_group, game)
                holder.z_index = sprite["z_index"]
                holder._id = sprite["id"]
                for image_id in sprite["deck"]:
                    holder.add_image(game.mp[image_id], False)
                game.mp[holder._id] = holder
            elif sprite["type"] == "player_hand":
                hand = game_module.PlayerHand(sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.sprite_group, game)
                hand._id = sprite["id"]
                game.mp[hand._id] = hand
        for sprite in game_state:
            if sprite["type"] == "shuffle_button":
                button = game_module.ShuffleButton(game.sprite_group, game, sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.mp[sprite["holder"]])
                button.z_index = sprite["z_index"]
                button._id = sprite["id"]
            elif sprite["type"] == "retrieve_button":
                images_to_retrieve = []
                for image_id in sprite["images_to_retrieve"]:
                    images_to_retrieve.append(game.mp[image_id])
                button = game_module.RetrieveButton(game.sprite_group, game, sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.mp[sprite["holder"]], images_to_retrieve)
                button.z_index = sprite["z_index"]
                button._id = sprite["id"]
            elif sprite["type"] == "dice":
                dice = game_module.Dice(sprite["paths"], sprite["x"], sprite["y"], sprite["width"], sprite["height"], game.sprite_group, game)
                dice.z_index = sprite["z_index"]
                dice._id = sprite["id"]
                dice.draggable = sprite["draggable"]
                dice.rotatable = sprite["rotatable"]
                dice.rotation = sprite["rotation"]
                game.mp[dice._id] = dice
                dice.update()
        game.initialize_z_index()

