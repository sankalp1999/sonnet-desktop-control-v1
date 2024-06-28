from anthropic import Anthropic
import os
from datetime import datetime
from PIL import Image
import io
import pyautogui
import base64
from colorama import init, Fore, Style
import tempfile


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

conversation_history = []

system_prompt = '''
You are Claude, an AI assistant that takes instructions from the user. 
User will give you instruction to perform tasks on their computer. You can take screenshot, move the cursor and click items on the screen.

You can do three operations
1. Take screenshot after every user's input and carefully analyze the image. Estimate position of objects that user mentions accurately.
2. Move the cursor and click.
3. Type

'''


# def encode_image_to_base64(image_path):
#     try:
#         with Image.open(image_path) as img:
#             # Convert image to RGB if it's not
#             if img.mode != 'RGB':
#                 img = img.convert('RGB')
#             img_byte_arr = io.BytesIO()
#             img.save(img_byte_arr, format='JPEG', quality=95)  # Save as JPEG
#             return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
#     except Exception as e:
#         return f"Error encoding image: {str(e)}"

from PIL import ImageGrab
import io
import os
from datetime import datetime
import base64

def take_screenshot(tool_id):
    # Take a screenshot using PIL
    screenshot = ImageGrab.grab()
    
    # Define the maximum size
    max_size = 1568
    
    # Get the original dimensions
    width, height = screenshot.size
    
    # Calculate the scaling factor
    scale = min(max_size / width, max_size / height)
    
    # If the image is already smaller than max_size, don't upscale
    if scale >= 1:
        resized_screenshot = screenshot
    else:
        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize the image
        resized_screenshot = screenshot.resize((new_width, new_height), Image.LANCZOS)
    
    # Create a directory to store screenshots if it doesn't exist
    screenshot_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Generate a unique filename based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.jpg"
    filepath = os.path.join(screenshot_dir, filename)
    
    # Save the resized screenshot as JPEG
    resized_screenshot = resized_screenshot.convert('RGB')  # Convert to RGB mode for JPEG
    resized_screenshot.save(filepath, format='JPEG', quality=95)  # Save as JPEG with high quality
    
    # Encode the image to base64
    with io.BytesIO() as buffer:
        resized_screenshot.save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    tool_result_message = [
        {
            "type": "text",
            "text": f"Screenshot captured {filename}. Original size: {width}x{height}, Resized to: {resized_screenshot.size[0]}x{resized_screenshot.size[1]}"
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
    
    print(f"Resized screenshot saved to: {filepath}")
    
    return tool_result_message

def encode_image_to_base64(image_path):
    try:
        with Image.open(image_path) as img:
            # Convert image to RGB if it's not
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=100)  # Save as JPEG
            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    except Exception as e:
        return f"Error encoding image: {str(e)}"




def move_and_click(x, y, duration=2):
    # Hard-coded scaling factor (adjust this based on your typical screenshot size)
    scale_factor = 1.1  # This is an example value, adjust as needed
    
    scaled_x = int(x * scale_factor)
    scaled_y = int(y * scale_factor)
    
    pyautogui.moveTo(scaled_x, scaled_y, duration=duration)
    pyautogui.doubleClick()
    return f"Moved to scaled coordinates ({scaled_x}, {scaled_y}) and clicked"

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
    global conversation_history

    print(f"\n{'='*50}\nUser Message: {user_input}\n{'='*50}")

    conversation_history.append({"role": "user", "content": user_input})
    
    messages = [msg for msg in conversation_history if msg.get('content')]

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
    print(f"Stop Reason: {response.stop_reason}")
    print(f"Content: {response.content}")

    assistant_response = ""

    while response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")
        tool_name = tool_use.name
        tool_input = tool_use.input
        tool_use_id = tool_use.id

        print(f"\nTool Used: {tool_name}")
        # print(f"Tool Input:")
        # print(json.dumps(tool_input, indent=2))

        result = execute_tool(tool_name, tool_input)

        # print(f"\nTool Result:")
        # print(json.dumps(result, indent=2))
        print(f"\n", tool_use)

        conversation_history.append({"role": "assistant", "content": [tool_use]})
        conversation_history.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result
                }
            ]
        })

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                system=system_prompt,
                messages=[msg for msg in conversation_history if msg.get('content')],
                tools=tools,
                tool_choice={"type": "auto"}
            )

            # print(f"\nResponse:")
            # print(f"Stop Reason: {response.stop_reason}")
            print(f"Content: {response.content}")

        except Exception as e:
            print(f"Error in tool response: {str(e)}")
            assistant_response += "\nI encountered an error while processing the tool result. Please try again."
            break

    final_response = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )

    if final_response:
        assistant_response += final_response
        conversation_history.append({"role": "assistant", "content": final_response})

    print(f"\nFinal Response: {assistant_response}")

    return assistant_response


def main():
    print_colored("Welcome anon", CLAUDE_COLOR)
    print_colored("Type 'exit' to end the conversation.", CLAUDE_COLOR)
    print_colored("To include an image, type 'image' and press enter. Then drag and drop the image into the terminal.", CLAUDE_COLOR)
    
    while True:
        user_input = input(f"\n{USER_COLOR}You: {Style.RESET_ALL}")
        
        if user_input.lower() == 'exit':
            print_colored("Thanks, goodbye.", CLAUDE_COLOR)
            break
        
        if user_input.lower() == 'image':
            image_path = input(f"{USER_COLOR}Drag and drop your image here: {Style.RESET_ALL}").strip().replace("'", "")
            
            if os.path.isfile(image_path):
                user_input = input(f"{USER_COLOR}You (prompt for image): {Style.RESET_ALL}")
                response = chat_with_claude(user_input, image_path)
            else:
                print_colored("Invalid image path. Please try again.", CLAUDE_COLOR)
                continue
        else:
            response = chat_with_claude(user_input)
        
        if response.startswith("Error") or response.startswith("Sorry we encountered an error communicating with the AI."):
            print_colored(response, TOOL_COLOR)

if __name__ == "__main__":
    main()