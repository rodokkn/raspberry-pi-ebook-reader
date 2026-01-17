#!/home/ebook/reader/bin/python3
import fitz, os, json, math, time
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2, epdconfig
import RPi.GPIO as GPIO

# -----------------------------
# Directory configuration
# -----------------------------

# Folder containing input PDF files
PDF_FOLDER = os.path.expanduser(
    "~/e-Paper/RaspberryPi_JetsonNano/python/examples/pdf_first"
)

# Folder for generated TXT files
TXT_FOLDER = os.path.expanduser(
    "~/e-Paper/RaspberryPi_JetsonNano/python/examples/pdf_first_txt"
)

# Cache directory for preprocessed text lines
CACHE_FOLDER = os.path.join(TXT_FOLDER, "cache")

os.makedirs(TXT_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

# -----------------------------
# Font configuration
# -----------------------------

FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_SIZE = 18

# -----------------------------
# Capacitive button GPIO pins (BCM numbering)
# -----------------------------

BUTTONS = {
    'A': 5,   # Page backward
    'D': 6,   # Page forward
    'M': 13   # Menu / back
}

# GPIO setup
GPIO.setmode(GPIO.BCM)
for pin in BUTTONS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# -----------------------------
# Reading progress storage
# ----------------------------

PROGRESS_FILE = os.path.join(TXT_FOLDER, "progress.json")

def load_progress():
    """Load last read page information from disk."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress):
    """Save current reading progress to disk."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

# -----------------------------
# Automatic PDF to TXT conversion
# -----------------------------

def convert_pdfs_to_txt():
    """Convert all PDF files in the input folder to TXT format."""
    for pdf_file in os.listdir(PDF_FOLDER):
        if pdf_file.lower().endswith(".pdf"):
            txt_file = os.path.join(
                TXT_FOLDER, pdf_file.rsplit(".", 1)[0] + ".txt"
            )
            if os.path.exists(txt_file):
                continue

            pdf_path = os.path.join(PDF_FOLDER, pdf_file)
            doc = fitz.open(pdf_path)

            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"

            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(text)

# -----------------------------
# TXT file handling
# -----------------------------

def list_txt():
    """List all available TXT files."""
    return [f for f in os.listdir(TXT_FOLDER) if f.lower().endswith(".txt")]

def load_lines(txt_path, width, height, font):
    """
    Load text lines from a TXT file.
    Uses cached line data if available to improve performance.
    """
    base_name = os.path.splitext(os.path.basename(txt_path))[0]
    cache_file = os.path.join(CACHE_FOLDER, base_name + ".lines.json")

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            lines = json.load(f)
    else:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = " ".join(f.read().split())

        img_temp = Image.new("L", (width, height))
        draw = ImageDraw.Draw(img_temp)

        max_width = width - 20
        line_height = FONT_SIZE + 4

        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            w, h = draw.textbbox((0, 0), test_line, font=font)[2:]
            if w < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(lines, f)

    return lines

# -----------------------------
# Page rendering
# -----------------------------

def render_text_page(lines, subpage_number, width, height, font):
    """
    Render a single page of text and return the image along with
    the total number of pages.
    """
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    x, y = 10, 10
    line_height = FONT_SIZE + 4
    reserved_space = line_height + 5

    lines_per_page = max(
        (height - reserved_space - 2 * 10) // line_height, 1
    )
    total_pages = math.ceil(len(lines) / lines_per_page)

    start = subpage_number * lines_per_page
    end = min(start + lines_per_page, len(lines))

    y_cursor = y
    for line in lines[start:end]:
        draw.text((x, y_cursor), line, font=font, fill=0)
        y_cursor += line_height

    draw.text(
        (10, height - line_height - 5),
        f"{subpage_number + 1}/{total_pages}",
        font=font,
        fill=0
    )

    return img.convert("1"), total_pages

# -----------------------------
# Button handling
# -----------------------------

def wait_for_button():
    """Wait until a button is pressed."""
    while True:
        if GPIO.input(BUTTONS['A']):
            time.sleep(0.05)
            return 'A'
        if GPIO.input(BUTTONS['D']):
            time.sleep(0.05)
            return 'D'
        if GPIO.input(BUTTONS['M']):
            time.sleep(0.05)
            return 'M'
        time.sleep(0.01)

# -----------------------------
# TXT file selection menu
# -----------------------------

def select_txt(epd, txts):
    """Display a simple menu for TXT file selection."""
    menu = txts + ["Exit"]
    index = 0
    last_displayed = None

    width, height = min(epd.width, epd.height), max(epd.width, epd.height)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    while True:
        img = Image.new("1", (width, height), 255)
        draw = ImageDraw.Draw(img)

        y = 50
        for i, name in enumerate(menu):
            prefix = "> " if i == index else "  "
            draw.text((50, y), prefix + name, font=font, fill=0)
            y += FONT_SIZE + 10

        if last_displayed != index:
            epd.display(epd.getbuffer(img))
            last_displayed = index

        btn = wait_for_button()
        if btn == 'D':
            index = (index + 1) % len(menu)
        elif btn == 'A':
            index = (index - 1) % len(menu)
        elif btn == 'M':
            if menu[index] == "Exit":
                epd.Clear()
                epd.sleep()
                exit()
            return os.path.join(TXT_FOLDER, menu[index])

# -----------------------------
# TXT viewing loop
# -----------------------------

def view_txt(epd, txt_path, progress, font):
    """Display a TXT file and handle page navigation."""
    width, height = min(epd.width, epd.height), max(epd.width, epd.height)
    lines = load_lines(txt_path, width, height, font)

    filename = os.path.basename(txt_path)
    subpage_number = progress.get(filename, 0)
    last_displayed = None

    while True:
        page_img, total_pages = render_text_page(
            lines, subpage_number, width, height, font
        )

        if last_displayed != subpage_number:
            epd.display(epd.getbuffer(page_img))
            last_displayed = subpage_number

        btn = wait_for_button()
        if btn == 'D' and subpage_number < total_pages - 1:
            subpage_number += 1
        elif btn == 'A' and subpage_number > 0:
            subpage_number -= 1
        elif btn == 'M':
            progress[filename] = subpage_number
            save_progress(progress)
            break

# -----------------------------
# Main entry point
# -----------------------------

def main():
    epdconfig.GPIO_PWR_PIN = 8
    epd = epd7in5_V2.EPD()
    epd.init()

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    convert_pdfs_to_txt()
    progress = load_progress()
    txts = list_txt()

    if not txts:
        epd.Clear()
        epd.sleep()
        return

    while True:
        txt_path = select_txt(epd, txts)
        view_txt(epd, txt_path, progress, font)

    epd.Clear()
    epd.sleep()

if __name__ == "__main__":
    main()
