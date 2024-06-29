from anthropic import Anthropic
import os
from datetime import datetime
from PIL import Image, ImageGrab
import io
import pyautogui
import base64
from colorama import init, Fore, Style
import cv2
import numpy as np

client = Anthropic(api_key=os.environ.get("API_KEY"))


# Initialize colorama
init()

# Color constants
USER_COLOR = Fore.WHITE
CLAUDE_COLOR = Fore.BLUE
TOOL_COLOR = Fore.YELLOW
RESULT_COLOR = Fore.GREEN

# Helper function to print colored text
def print_colored(text, color):
    print(f"{color}{text}{Style.RESET_ALL}")

messages = []

system_prompt = '''
You are Claude, an AI assistant capable of controlling the user's computer through specific function calls. Your primary functions are:

Take and analyze screenshots:

If you lack information, request a new screenshot.
Carefully analyze screenshots, paying special attention to the coordinate grid overlay.

SEE CAREFULLY WHICH X axis and Y axis line is passing through the UI element to get the coordinate. Don't estimate. Tell based on what you see.
Determine the center position of the element, not just its edges.

Use existing screenshot information when available.


Move the cursor and click:

Use precise coordinates derived from the grid overlay.
Aim for the center of UI elements for more reliable interactions.


Type text as instructed.

Guidelines for operation:

- Think carefully before selecting which tools to use.
- Follow user instructions precisely to identify buttons and UI elements.
- Minimize unnecessary navigation; focus on direct actions when possible.
- When identifying UI elements, refer to the coordinate grid overlay:

'''

def take_screenshot(tool_id):
    # Take a screenshot using PIL
    screenshot = ImageGrab.grab()
    
    # Resize the image to match UI scaling
    target_width, target_height = 1728, 1117
    screenshot = screenshot.resize((target_width, target_height), Image.LANCZOS)
    
    # Convert PIL image to numpy array for OpenCV processing
    screenshot_np = np.array(screenshot)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    # Define grid properties
    grid_size = 75  # Adjust this value to change the density of the grid
    color = (0, 255, 0)  # Green color for grid lines and labels
    thickness = 1  # Thickness of the grid lines
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.2
    font_thickness = 1
    
    # Draw vertical lines and add x-coordinates
    for x in range(0, target_width, grid_size):
        cv2.line(screenshot_np, (x, 0), (x, target_height), color, thickness)
        label = f"{x}"
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        cv2.putText(screenshot_np, label, (x - text_width//2, 20), font, 0.6, color, font_thickness)
    
    # Draw horizontal lines and add y-coordinates
    for y in range(0, target_height, grid_size):
        cv2.line(screenshot_np, (0, y), (target_width, y), color, thickness)
        label = f"{y}"
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        cv2.putText(screenshot_np, label, (5, y + text_height//2), font, font_scale, color, font_thickness)
    
    # Convert back to PIL Image
    screenshot_with_grid = Image.fromarray(cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2RGB))
    
    # Create a directory to store screenshots if it doesn't exist
    screenshot_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Generate a unique filename based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_with_grid_{timestamp}.jpg"
    filepath = os.path.join(screenshot_dir, filename)
    
    # Save the screenshot with grid as JPEG
    screenshot_with_grid.save(filepath, format='JPEG', quality=95)
    
    # Encode the image to base64
    with io.BytesIO() as buffer:
        screenshot_with_grid.save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    tool_result_message = [
        {
            "type": "text",
            "text": f"I have provided you the screenshot with a coordinate grid overlay. The image resolution is 1728x1117, matching your UI scaling. The grid coordinates correspond to this resolution. Please analyze carefully."
        },
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_base64
            }
        }
    ]
    
    print(f"Screenshot with grid saved to: {filepath}")
    
    return tool_result_message


def move_and_click(x, y, duration=2):
    # Hard-coded scaling factor (adjust this based on your typical screenshot size)
    scale_factor = 1  # This is an example value, adjust as needed
    
    scaled_x = int(x * scale_factor)
    scaled_y = int(y * scale_factor)
    
    pyautogui.moveTo(scaled_x, scaled_y, duration=duration)
    pyautogui.doubleClick()
    return f"Moved to scaled coordinates ({scaled_x}, {scaled_y}) and clicked"


# def move_and_click(x, y, duration=2):
#     # Original screen dimensions
#     original_width, original_height = 3456, 2256
    
#     # Max size used for scaling the screenshot
#     max_size = 1568
    
#     # Calculate the scaling factor based on the longer edge
#     scale_factor = max(original_width, original_height) / max_size
    
#     # Scale the coordinates back up to the original screen size
#     scaled_x = int(x * scale_factor)
#     scaled_y = int(y * scale_factor)
    
#     # Ensure the scaled coordinates don't exceed the screen boundaries
#     scaled_x = min(scaled_x, original_width - 1)
#     scaled_y = min(scaled_y, original_height - 1)
    
#     pyautogui.moveTo(scaled_x, scaled_y, duration=duration)
#     pyautogui.doubleClick()
#     return f"Moved to scaled coordinates ({scaled_x}, {scaled_y}) and clicked"


def type_text(text, interval=0.1):
    pyautogui.write(text, interval=interval)
    return f"Typed: {text}"

tools = [
    {
        "name": "move_and_click",
        "description": "Move the cursor to a specified position and perform a click.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer",
                    "description": "The x-coordinate to move to"
                },
                "y": {
                    "type": "integer",
                    "description": "The y-coordinate to move to"
                },
                "duration": {
                    "type": "number",
                    "description": "The duration of the movement in seconds (optional, default: 2)"
                }
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "type_text",
        "description": "Type the specified text with an optional interval between keystrokes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to type"
                },
                "interval": {
                    "type": "number",
                    "description": "The interval between keystrokes in seconds (optional, default: 0.1)"
                }
            },
            "required": ["text"]
        }
    },
        {
        "name": "take_screenshot",
        "description": "Take a screenshot of the current screen and return both the file path and the image data for analysis. Send to claude before doing executing other tools",
        "input_schema": {
            "type": "object",
              "properties": {
                "tool_id": {
                    "type": "string",
                    "description": "tool id"
                }
            },
            "required": ["tool_id"]
        }
    }
]


def execute_tool(tool_name, tool_input):
    if tool_name == "move_and_click":
        return move_and_click(tool_input["x"], tool_input["y"], tool_input.get("duration", 4))
    elif tool_name == "type_text":
        return type_text(tool_input["text"], tool_input.get("interval", 0.1))
    elif tool_name == "take_screenshot":
        return take_screenshot(tool_input["tool_id"])
    else:
        return f"Unknown tool: {tool_name}"


def chat_with_claude(user_input, image_path=None):
    global messages

    print(f"\n{'='*50}\nUser Message: {user_input}\n{'='*50}")

    messages.append({"role": "user", "content": user_input})
    

    print("HERE")
    try:
         response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system=system_prompt,
            messages=messages,
            tools=tools,
            tool_choice={"type": "auto"}
        )
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        return "I'm sorry, there was an error communicating with the AI. Please try again."

    print(f"\nInitial Response:")

    print(response)


    # print(f"Stop Reason: {response.stop_reason}")
    # print(f"Content: {response.content}")

    assistant_response = ""
    messages.append({"role": "assistant", "content": response.content})

    for block in response.content:


        if block.type == "text":
            print(block)
            # messages.append({"role": "assistant", "content": [block]})
        
        elif block.type == "tool_use":
            tool_name = block.name
            tool_input = block.input
            tool_use_id = block.id
            result = execute_tool(tool_name, tool_input)


            print("here: ", tool_use_id)

        
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": result
                    }
                ]
            })

            

            if tool_name == "take_screenshot":

                print(f"Tool Used: {tool_name}")
                print("*******************************")
                # print(messages)
                print("*******************************")

                try:
                
                    second_response = response = client.messages.create(
                                model="claude-3-5-sonnet-20240620",
                                max_tokens=4000,
                                system=system_prompt,
                                messages=messages,
                                tools=tools,
                                tool_choice={"type": "auto"}
                            )

                    messages.append({"role": "assistant", "content": second_response.content})

                    for block in second_response.content:
                        if block.type == "text":
          
                            print(block)
                        elif block.type == "tool_use":
                            second_tool_name = block.name
                            second_tool_input = block.input
                            second_tool_use_id = block.id
                            second_result = execute_tool(second_tool_name, second_tool_input)

                            print("here: ", second_tool_use_id)

                        
                            messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": second_tool_use_id,
                                        "content": second_result
                                    }
                                ]
                            })
                            messages.append({"role": "assistant", "content": "I completed the operation."})

                    print("*******************************")
                    print(second_response.content)
                    print("*******************************")

                except Exception as e:
                    print(f"Error calling Claude API: {str(e)}")
                    return "I'm sorry, there was an error communicating with the AI. Please try again."
                
            else:
                messages.append({"role": "assistant", "content": "I completed the operation."})
                print(f"Tool Used: {tool_name}")

    return "all fine"


def main():
    print_colored("Welcome anon", CLAUDE_COLOR)
    print_colored("Type 'exit' to end the conversation.", CLAUDE_COLOR)
    print_colored("To include an image, type 'image' and press enter. Then drag and drop the image into the terminal.", CLAUDE_COLOR)
    
    while True:
        user_input = input(f"\n{USER_COLOR}You: {Style.RESET_ALL}")
        print("STUCK")
        if user_input.lower() == 'exit':
            print_colored("Thanks, goodbye.", CLAUDE_COLOR)
            break
        
        else:
            response = chat_with_claude(user_input)
        
        if response.startswith("Error") or response.startswith("Sorry we encountered an error communicating with the AI."):
            print_colored(response, TOOL_COLOR)

if __name__ == "__main__":
    main()