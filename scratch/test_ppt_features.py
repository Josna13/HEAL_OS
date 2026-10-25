import win32com.client
import sys
import os

try:
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    # ppt.Visible = True  # or False
    pres = ppt.Presentations.Add(True)  # True = with window, or False
    
    # 16:9 widescreen in points: 960 pt wide by 540 pt high (or 13.333 x 7.5 inches * 72)
    pres.PageSetup.SlideWidth = 960
    pres.PageSetup.SlideHeight = 540
    
    # 12 is ppLayoutBlank
    slide = pres.Slides.Add(1, 12)
    
    # Background color: RGB(11, 18, 32) -> In COM RGB is R + G*256 + B*65536
    def rgb(r, g, b):
        return r + (g << 8) + (b << 16)
        
    slide.FollowMasterBackground = False
    slide.Background.Fill.Solid()
    slide.Background.Fill.ForeColor.RGB = rgb(11, 18, 32)
    
    # Add a card shape
    # 1 is msoShapeRectangle, 5 is msoShapeRoundedRectangle
    card = slide.Shapes.AddShape(5, 50, 50, 400, 200) # msoShapeRoundedRectangle
    card.Fill.Solid()
    card.Fill.ForeColor.RGB = rgb(17, 28, 46)
    card.Line.ForeColor.RGB = rgb(38, 54, 77)
    card.Line.Weight = 1.5
    
    # Text in card
    tf = card.TextFrame
    tf.WordWrap = True
    tr = tf.TextRange
    tr.Text = "HealOS Architecture Card"
    tr.Font.Name = "Calibri"
    tr.Font.Size = 18
    tr.Font.Bold = True
    tr.Font.Color.RGB = rgb(34, 211, 238)
    
    # Speaker notes
    notes_page = slide.NotesPage
    # Placeholder 2 in notes page is usually the notes body
    for shp in notes_page.Shapes:
        if shp.HasTextFrame:
            # Check if it's the notes placeholder
            shp.TextFrame.TextRange.Text = "Speaker note: Welcome faculty members to the HealOS demonstration."
            break
            
    test_out = os.path.abspath(r"scratch\test_out.pptx")
    pres.SaveAs(test_out)
    pres.Close()
    ppt.Quit()
    print("Success! File saved to:", test_out)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
