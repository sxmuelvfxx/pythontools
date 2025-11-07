import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import svgwrite

# Characters to export
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,"

def export_glyphs_to_svg(font_path, output_dir, svg_size, progress_var, label_var):
    SVG_WIDTH, SVG_HEIGHT = svg_size

    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()

    # Find Unicode cmap
    cmap = None
    for table in font["cmap"].tables:
        if table.isUnicode():
            cmap = table.cmap
            break
    if not cmap:
        raise RuntimeError("No Unicode cmap found in the font.")

    # Font metrics for scaling
    head = font["head"]
    ascent = font["hhea"].ascent
    descent = font["hhea"].descent
    total_height = ascent - descent

    os.makedirs(output_dir, exist_ok=True)
    total_chars = len(CHARS)

    for i, char in enumerate(CHARS):
        glyph_name = cmap.get(ord(char))
        if not glyph_name:
            print(f"Skipping {char!r} — no glyph found.")
            continue

        glyph = glyph_set[glyph_name]
        pen = SVGPathPen(glyph_set)
        glyph.draw(pen)
        path_data = pen.getCommands()

        # Scale to fit SVG canvas height
        scale = SVG_HEIGHT / total_height

        filename = f"{'!' if char.isupper() else ''}{char}.svg"
        output_path = os.path.join(output_dir, filename)

        dwg = svgwrite.Drawing(
            filename=output_path,
            size=(f"{SVG_WIDTH}px", f"{SVG_HEIGHT}px"),
            viewBox=f"0 0 {SVG_WIDTH} {SVG_HEIGHT}"
        )

        # Left-aligned, baseline-aligned
        transform = f"translate(0,{SVG_HEIGHT * 0.9}) scale({scale},-{scale})"
        dwg.add(dwg.path(d=path_data, fill="black", transform=transform))
        dwg.save()

        # Update progress bar and label
        progress = (i + 1) / total_chars * 100
        progress_var.set(progress)
        label_var.set(f"Exporting: '{char}' ({i + 1}/{total_chars})")
        progress_var.widget.update_idletasks()

    messagebox.showinfo("Done", f"✅ SVGs saved in:\n{output_dir}")

def main():
    root = tk.Tk()
    root.withdraw()

    # Ask for font file
    font_path = filedialog.askopenfilename(
        title="Select a TTF or OTF font file",
        filetypes=[("Font files", "*.ttf *.otf")]
    )
    if not font_path:
        messagebox.showwarning("Cancelled", "No font selected.")
        return

    # Ask for output folder
    output_dir = filedialog.askdirectory(
        title="Select folder to save SVGs"
    )
    if not output_dir:
        messagebox.showwarning("Cancelled", "No output folder selected.")
        return

    # Ask for SVG size
    size_input = simpledialog.askinteger(
        "SVG Size",
        "Enter SVG size in pixels (e.g. 1000 for 1000×1000):",
        minvalue=100,
        maxvalue=10000
    )
    if not size_input:
        messagebox.showwarning("Cancelled", "No size entered.")
        return

    svg_size = (size_input, size_input)

    # Progress bar window
    progress_win = tk.Toplevel()
    progress_win.title("Exporting SVGs...")
    progress_win.geometry("400x130")
    progress_win.resizable(False, False)

    label_var = tk.StringVar(value="Starting export...")
    tk.Label(progress_win, textvariable=label_var).pack(pady=10)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", padx=20, pady=10)
    progress_var.widget = progress_bar  # attach widget reference

    try:
        export_glyphs_to_svg(font_path, output_dir, svg_size, progress_var, label_var)
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        progress_win.destroy()

if __name__ == "__main__":
    main()
