from Algorithm.mdpalgo.constants import mdp_constants
from Algorithm.mdpalgo.interface.buttons import Button


class Panel(object):

    def __init__(self, surface):
        self.surface = surface

        # Buttons
        self.buttons = []

        connect_button = Button(surface, mdp_constants.GREEN, 650, 210, 150, 25, "Connect to RPI", mdp_constants.BLACK, "CONNECT")
        self.buttons.append(connect_button)
        disconnect_button = Button(surface, mdp_constants.LIGHT_RED, 650, 240, 150, 25, "Disconnect from RPI", mdp_constants.BLACK, "DISCONNECT")
        self.buttons.append(disconnect_button)

        # For testing
        forward_button = Button(surface, mdp_constants.LIGHT_GREEN, 650, 270, 150, 25, "Forward", mdp_constants.BLACK, "FORWARD")
        self.buttons.append(forward_button)
        backward_button = Button(surface, mdp_constants.LIGHT_GREEN, 650, 300, 150, 25, "Backward", mdp_constants.BLACK, "BACKWARD")
        self.buttons.append(backward_button)
        for_right_button = Button(surface, mdp_constants.LIGHT_GREEN, 650, 330, 150, 25, "Forward Right", mdp_constants.BLACK, "FORWARD_RIGHT")
        self.buttons.append(for_right_button)
        for_left_button = Button(surface, mdp_constants.LIGHT_GREEN, 650, 360, 150, 25, "Forward Left", mdp_constants.BLACK, "FORWARD_LEFT")
        self.buttons.append(for_left_button)
        back_right_button = Button(surface, mdp_constants.LIGHT_GREEN, 650, 390, 150, 25, "Backward Right", mdp_constants.BLACK, "BACKWARD_RIGHT")
        self.buttons.append(back_right_button)
        back_left_button = Button(surface, mdp_constants.LIGHT_GREEN, 650, 420, 150, 25, "Backward Left", mdp_constants.BLACK, "BACKWARD_LEFT")
        self.buttons.append(back_left_button)

        reset_button = Button(surface, mdp_constants.RED, 460, 80, 100, 25, "RESET", mdp_constants.BLACK, "RESET")
        self.buttons.append(reset_button)
        start_button = Button(surface, mdp_constants.GREEN, 120, 80, 100, 25, "START", mdp_constants.BLACK, "START")
        self.buttons.append(start_button)

    def redraw_buttons(self):
        for button in self.buttons:
            button.draw_button(button.surface, button.color, button.length, button.height, button.x, button.y, button.width)
            button.write_text(button.surface, button.text, button.text_color, button.length, button.height, button.x, button.y)

    def button_clicked(self, button):
        return button.pressed()

    def get_button_clicked(self, button):
        return button.get_function()
