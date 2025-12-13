import streamlit as st
from fpdf import FPDF
import tempfile
from PIL import Image
import os

class PDF(FPDF):
    def header(self):
        # Set font for the header
        self.set_font('Arial', 'B', 12)
        # We generally handle headers manually in the body for this specific layout
        # to ensure they appear exactly where the table starts, 
        # but you can add a global title here if needed.
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(images, header_text="pic"):
    # A4 Landscape dimensions: 297mm width x 210mm height
    pdf = PDF(orientation='L', unit='mm', format='A4')
    
    # Settings for the layout
    margin = 10
    col_width_img = 80  # Width of the first column (image column)
    col_width_other = 190 # Width of the rest of the page
    row_height = 90     # Height allocated for each image row
    
    pdf.set_margins(margin, margin, margin)
    
    # Process images in chunks of 2 (since we want 2 per page)
    for i in range(0, len(images), 2):
        pdf.add_page()
        
        # --- Draw Table Headers ---
        pdf.set_font('Arial', 'B', 12)
        
        # Header for Image Column
        pdf.cell(col_width_img, 10, header_text, border=1, align='C')
        
        # Header for the "Rest" (Empty columns based on your sheet structure)
        # You can split this into multiple cells if you want to match the "---" columns exactly
        pdf.cell(col_width_other, 10, "Notes / Data", border=1, align='L')
        
        pdf.ln() # Move to next line
        
        # --- Draw Rows ---
        # We need to handle the current batch of 2 images
        batch = images[i:i+2]
        
        for img_file in batch:
            # Save current coordinates
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            
            # 1. Draw the Image Cell Border
            pdf.rect(x_start, y_start, col_width_img, row_height)
            
            # 2. Insert the Image
            # We save the uploaded file to a temp path so FPDF can read it
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                # Convert to RGB to avoid PNG alpha channel issues in FPDF
                pil_image = Image.open(img_file).convert('RGB')
                pil_image.save(tmp.name)
                
                # Calculate aspect ratio to fit image inside the cell nicely
                # We add a small padding (e.g., 2mm) inside the cell
                pdf.image(tmp.name, x=x_start+2, y=y_start+2, w=col_width_img-4, h=row_height-4, type='JPG')
                
                # Clean up temp file
                tmp_path = tmp.name
            
            os.remove(tmp_path)
            
            # 3. Draw the "Other Data" Cell Border (Empty for now)
            pdf.set_xy(x_start + col_width_img, y_start)
            pdf.cell(col_width_other, row_height, "", border=1)
            
            # Move cursor to the start of the next row
            pdf.set_xy(x_start, y_start + row_height)

    return pdf

# --- Streamlit UI ---
st.set_page_config(page_title="Image to PDF Landscape", layout="wide")

st.title("📸 Landscape PDF Generator")
st.markdown("""
This tool takes your uploaded photos and places **2 photos per page** in the **first column** of an A4 Landscape PDF.
""")

# 1. Header Input
col_header = st.text_input("First Column Header Name", value="pic")

# 2. File Uploader
uploaded_files = st.file_uploader("Upload images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"Uploaded {len(uploaded_files)} images.")
    
    if st.button("Generate PDF"):
        with st.spinner("Generating PDF..."):
            try:
                # Generate the PDF object
                pdf = generate_pdf(uploaded_files, header_text=col_header)
                
                # Save to a temporary buffer
                # FPDF's output() returns a string in Python 2, but bytes in Python 3 if dest='S'
                # However, simplest way for streamlit is to save to a temp file then read bytes
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    pdf.output(tmp_pdf.name)
                    
                    with open(tmp_pdf.name, "rb") as f:
                        pdf_bytes = f.read()
                    
                # Create Download Button
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name="landscape_photos.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

else:
    st.info("Please upload images to start.")

