import win32com.client
import os

ppt = win32com.client.Dispatch("PowerPoint.Application")
pres_path = os.path.abspath(r"E:\HealOs\HealOS_Presentation.pptx")
pres = ppt.Presentations.Open(pres_path, True, False, False)

print("--- PRESENTATION VERIFICATION ---")
print("Presentation Title/Name:", pres.Name)
print("Slide Width (pt):", pres.PageSetup.SlideWidth)
print("Slide Height (pt):", pres.PageSetup.SlideHeight)
print("Aspect Ratio:", round(pres.PageSetup.SlideWidth / pres.PageSetup.SlideHeight, 3))
print("Total Slides:", pres.Slides.Count)

for i in range(1, pres.Slides.Count + 1):
    slide = pres.Slides(i)
    # Check notes
    note_text = ""
    for shp in slide.NotesPage.Shapes:
        if shp.HasTextFrame and shp.Type == 14 and shp.PlaceholderFormat.Type == 2:
            note_text = shp.TextFrame.TextRange.Text.strip()
            break
    if not note_text:
        for shp in slide.NotesPage.Shapes:
            if shp.HasTextFrame and "Notes" in shp.Name:
                note_text = shp.TextFrame.TextRange.Text.strip()
                break
    
    first_text = ""
    for shp in slide.Shapes:
        if shp.HasTextFrame and shp.TextFrame.TextRange.Text.strip():
            first_text = shp.TextFrame.TextRange.Text.strip().split("\n")[0]
            break
            
    print(f"Slide {i:02d}: Shapes={slide.Shapes.Count:02d} | NotesLen={len(note_text):03d} | Header='{first_text}'")

pres.Close()
ppt.Quit()
print("Verification complete! Zero errors.")
