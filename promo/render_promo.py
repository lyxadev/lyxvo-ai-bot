import bpy
import math
import os
import sys

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
SIZES = [
    ("og_1200x630", 1200, 630),
    ("square_1080x1080", 1080, 1080),
    ("github_social_1280x640", 1280, 640),
]
LINES = ["Lyxvo.ai", "lyxvo-ai[bot]"]


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_gradient_material(name="LyxvoGradient"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    ramp = nodes.new("ShaderNodeValToRGB")

    # Lyxvo brand gradient: deep purple to hot pink
    ramp.color_ramp.elements[0].color = (0.42, 0.10, 0.85, 1.0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (1.00, 0.30, 0.66, 1.0)
    ramp.color_ramp.elements[1].position = 1.0

    links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.35
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Emission Strength"].default_value = 0.4
    links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_background():
    world = bpy.data.worlds.new("LyxvoWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.04, 0.02, 0.10, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = world


def add_text(body, text, location, size, mat):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.active_object
    obj.data.body = text
    obj.data.size = size
    obj.data.extrude = 0.12
    obj.data.bevel_depth = 0.01
    obj.data.bevel_resolution = 3
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.font = bpy.data.fonts.get("Bfont Regular") or obj.data.font
    obj.data.materials.append(mat)
    obj.name = body
    return obj


def add_camera_and_light(width, height):
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (0, -9, 0)
    cam.rotation_euler = (math.radians(90), 0, 0)
    cam_data.lens = 50
    # Fit horizontal frame width to the text block
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36
    bpy.context.scene.camera = cam

    for loc, energy in [((4, -6, 6), 2500), ((-5, -4, 3), 1200)]:
        ld = bpy.data.lights.new("Light", type="AREA")
        ld.energy = energy
        ld.size = 8
        lo = bpy.data.objects.new("Light", ld)
        bpy.context.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (math.radians(60), 0, math.radians(30))


def setup_render(width, height, out_path):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = out_path


def render_size(name, width, height):
    clear_scene()
    mat = make_gradient_material()
    make_background()
    # Scale text block relative to frame: smaller frames get smaller type
    base = min(width, height) / 1080.0
    add_text("Title", "Lyxvo.ai", (0, 0.9, 0), 1.6 * base, mat)
    add_text("Handle", "lyxvo-ai[bot]", (0, -1.0, 0), 0.9 * base, mat)
    add_camera_and_light(width, height)
    out_path = os.path.join(OUT_DIR, f"lyxvo_{name}.png")
    setup_render(width, height, out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[lyxvo] wrote {out_path}")


if __name__ == "__main__":
    for name, w, h in SIZES:
        render_size(name, w, h)
