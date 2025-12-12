import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders as gls
import glm
import numpy as np
import ctypes
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

windowSize = [800, 600]
cameraPos = glm.vec3(0, 2, 5)
cameraFront = glm.vec3(0, 0, -1)
cameraUp = glm.vec3(0, 1, 0)
yaw = -90.0
pitch = 0.0
lastX = 400
lastY = 300
firstMouse = True

deltaTime = 0.0
lastFrame = 0.0

# -----------------------------------------------------------
# GERA BLOCO (chão, paredes e topo com cores diferentes)
# permite omitir faces para criar aberturas (open_faces)
# faces indices: 0=front,1=back,2=left,3=right,4=bottom,5=top
# -----------------------------------------------------------
def generateBlock(width, height, depth, colorFloor, colorWall, colorTop, open_faces=None):
    if open_faces is None:
        open_faces = set()
    x = width / 2
    y = height / 2
    z = depth / 2

    faces = [
        # frente (0) - wall
        ([-x,-y,-z,  x,-y,-z,  x, y,-z,   x, y,-z, -x, y,-z, -x,-y,-z], colorWall),
        # trás (1) - wall
        ([-x,-y, z,  x,-y, z,  x, y, z,   x, y, z, -x, y, z, -x,-y, z], colorWall),
        # esquerda (2) - wall
        ([-x, y, z, -x, y,-z, -x,-y,-z,  -x,-y,-z, -x,-y, z, -x, y, z], colorWall),
        # direita (3) - wall
        ([x, y, z,  x, y,-z,  x,-y,-z,   x,-y,-z,  x,-y, z,  x, y, z], colorWall),
        # baixo (4) - floor
        ([-x,-y,-z, x,-y,-z, x,-y, z,   x,-y, z, -x,-y, z, -x,-y,-z], colorFloor),
        # cima (5) - top
        ([-x, y,-z, x, y,-z, x, y, z,   x, y, z, -x, y, z, -x, y,-z], colorTop),
    ]

    vertices = []
    for idx, (coords, col) in enumerate(faces):
        if idx in open_faces:
            continue  # cria abertura nessa face
        r, g, b = col
        for i in range(0, len(coords), 3):
            vertices += [coords[i], coords[i+1], coords[i+2], r, g, b]

    vertices = np.array(vertices, dtype=np.float32)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    stride = 6 * 4
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
    glEnableVertexAttribArray(1)

    glBindVertexArray(0)
    count = int(len(vertices) / 6)
    return vao, count

# -----------------------------------------------------------
# MIRA (NDC)
# -----------------------------------------------------------
def generateCrosshair(size=0.03):
    verts = np.array([
        -size, 0.0,
         size, 0.0,
         0.0, -size,
         0.0,  size,
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_STATIC_DRAW)

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2*4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glBindVertexArray(0)
    return vao

CROSS_VS = """
#version 330 core
layout(location=0) in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }
"""

CROSS_FS = """
#version 330 core
out vec4 FragColor;
void main(){ FragColor = vec4(1.0, 0.85, 0.1, 1.0); }
"""

# -----------------------------------------------------------
# CAMERA
# -----------------------------------------------------------
def mouse_callback(window, xpos, ypos):
    global firstMouse, lastX, lastY, yaw, pitch, cameraFront
    if firstMouse:
        lastX = xpos
        lastY = ypos
        firstMouse = False
    xoffset = xpos - lastX
    yoffset = lastY - ypos
    lastX = xpos
    lastY = ypos
    sensitivity = 0.1
    yaw += xoffset * sensitivity
    pitch += yoffset * sensitivity
    pitch = max(-89, min(89, pitch))
    direction = glm.vec3(
        glm.cos(glm.radians(yaw))*glm.cos(glm.radians(pitch)),
        glm.sin(glm.radians(pitch)),
        glm.sin(glm.radians(yaw))*glm.cos(glm.radians(pitch))
    )
    cameraFront = glm.normalize(direction)

def processInput(window):
    global cameraPos
    speed = 3 * deltaTime
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS: cameraPos += cameraFront * speed
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS: cameraPos -= cameraFront * speed
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS: cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp))*speed
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS: cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp))*speed

# -----------------------------------------------------------
# SHADER 3D DO USUÁRIO
# -----------------------------------------------------------
def loadShaderProgram():
    with open("vertex.glsl") as f:
        vertex = f.read()
    with open("fragment.glsl") as f:
        frag = f.read()
    return gls.compileProgram(
        gls.compileShader(vertex, GL_VERTEX_SHADER),
        gls.compileShader(frag, GL_FRAGMENT_SHADER)
    )

# -----------------------------------------------------------
# RENDER
# -----------------------------------------------------------
def render(shader, blocks, crossShader, crossVAO):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glUseProgram(shader)
    view = glm.lookAt(cameraPos, cameraPos+cameraFront, cameraUp)
    proj = glm.perspective(glm.radians(60), windowSize[0]/windowSize[1], 0.1, 200)
    glUniformMatrix4fv(glGetUniformLocation(shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
    glUniformMatrix4fv(glGetUniformLocation(shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj))

    modelLoc = glGetUniformLocation(shader, "model")

    for vao, count, pos in blocks:
        glBindVertexArray(vao)
        model = glm.translate(glm.mat4(1), pos)
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm.value_ptr(model))
        glDrawArrays(GL_TRIANGLES, 0, count)

    glDisable(GL_DEPTH_TEST)
    glUseProgram(crossShader)
    glBindVertexArray(crossVAO)
    glDrawArrays(GL_LINES, 0, 4)
    glEnable(GL_DEPTH_TEST)

# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------
def main():
    global deltaTime, lastFrame
    glfw.init()
    window = glfw.create_window(windowSize[0], windowSize[1], "Mapa Conectado", None, None)
    glfw.make_context_current(window)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glEnable(GL_DEPTH_TEST)

    shader = loadShaderProgram()

    # Cores distintas
    floorC  = (0.3, 0.3, 0.35)
    wallC   = (0.6, 0.1, 0.1)
    topC    = (0.4, 0.4, 0.45)

    blocks = []

    # Bloco 1
    b1, c1 = generateBlock(8, 1, 8, floorC, wallC, topC)
    blocks.append((b1, c1, glm.vec3(-10, 0, 0)))
    # Bloco 2
    b2, c2 = generateBlock(8, 1, 8, floorC, wallC, topC)
    blocks.append((b2, c2, glm.vec3(10, 0, 0)))
    # Corredor ligando com aberturas: corredor central e omitir faces nas plataformas para abrir passagens
    # Plataforma esquerda omite face 'right' (3), direita omite face 'left' (2)
    # Corredor omite front (0) and back (1) accordingly to create openings on both ends
    p1, pc1 = generateBlock(8, 1, 8, floorC, wallC, topC, open_faces={3})
    # actually p1 duplicates b1 but with opening; to keep simple replace b1
    blocks[-2] = (p1, pc1, glm.vec3(-10,0,0))

    p2, pc2 = generateBlock(8, 1, 8, floorC, wallC, topC, open_faces={2})
    blocks[-1] = (p2, pc2, glm.vec3(10,0,0))

    # Corredor central menor (depth = 12) connecting x=-10 to x=10, centered at x=0
    corridor, cc = generateBlock(20, 1, 6, floorC, wallC, topC, open_faces={0,1})
    blocks.append((corridor, cc, glm.vec3(0,0,0)))

    # cria mira
    crossVAO = generateCrosshair(0.03)

    # compila shader da mira
    crossShader = gls.compileProgram(
        gls.compileShader(CROSS_VS, GL_VERTEX_SHADER),
        gls.compileShader(CROSS_FS, GL_FRAGMENT_SHADER)
    )

    while not glfw.window_should_close(window):
        currentFrame = glfw.get_time()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        glfw.poll_events()
        processInput(window)

        render(shader, blocks, crossShader, crossVAO)

        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()
