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

def generate_pdf(item_details, header_text="pic"):
    # A4 Landscape dimensions: 297mm width x 210mm height
    pdf = PDF(orientation='L', unit='mm', format='A4')
    
    # Settings for the layout
    margin = 10
    col_width_img = 60   # Width of the image column
    col_width_name = 40  # Width of the name column
    col_width_price = 30 # Width of the price column
    col_width_qty = 30   # Width of the quantity column
    col_width_notes = 107 # Width of the notes column
    row_height = 90     # Height allocated for each image row
    
    pdf.set_margins(margin, margin, margin)
    
    # Process items in chunks of 2 (since we want 2 per page)
    for i in range(0, len(item_details), 2):
        pdf.add_page()
        
        # --- Draw Table Headers ---
        pdf.set_font('Arial', 'B', 12)
        
        # Header cells
        pdf.cell(col_width_img, 10, header_text, border=1, align='C')
        pdf.cell(col_width_name, 10, "Name", border=1, align='C')
        pdf.cell(col_width_price, 10, "Price", border=1, align='C')
        pdf.cell(col_width_qty, 10, "Quantity", border=1, align='C')
        pdf.cell(col_width_notes, 10, "Notes", border=1, align='C')
        
        pdf.ln() # Move to next line
        
        # --- Draw Rows ---
        # We need to handle the current batch of 2 items
        batch = item_details[i:i+1]
        
        for item in batch:
            img_file = item['image']
            name = item['name']
            price = item['price']
            quantity = item['quantity']
            notes = item['notes']
            
            # Save current coordinates
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            
            # 1. Draw the Image Cell Border and Insert Image
            pdf.rect(x_start, y_start, col_width_img, row_height)
            
            # Insert the Image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                pil_image = Image.open(img_file).convert('RGB')
                pil_image.save(tmp.name)
                
                # Get image dimensions
                img_width, img_height = pil_image.size
                
                # Cell dimensions (with padding)
                cell_w = col_width_img - 4
                cell_h = row_height - 4
                
                # Calculate scale to fit image inside cell while maintaining aspect ratio
                scale = min(cell_w / img_width, cell_h / img_height)
                new_w = img_width * scale
                new_h = img_height * scale
                
                # Center the image in the cell
                x_img = x_start + 2 + (cell_w - new_w) / 2
                y_img = y_start + 2 + (cell_h - new_h) / 2
                
                pdf.image(tmp.name, x=x_img, y=y_img, w=new_w, h=new_h, type='JPG')
                
                # Clean up temp file
                tmp_path = tmp.name
            
            os.remove(tmp_path)
            
            # 2. Draw the Other Cells
            pdf.set_xy(x_start + col_width_img, y_start)
            pdf.cell(col_width_name, row_height, name, border=1, align='L')
            pdf.cell(col_width_price, row_height, price, border=1, align='L')
            pdf.cell(col_width_qty, row_height, quantity, border=1, align='L')
            pdf.cell(col_width_notes, row_height, notes, border=1, align='L')
            
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
    
    # Collect details for each image
    item_details = []
    for i, img_file in enumerate(uploaded_files):
        st.subheader(f"Details for Image {i+1}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            name = st.text_input(f"Name {i+1}", key=f"name_{i}")
        with col2:
            price = st.text_input(f"Price {i+1}", key=f"price_{i}")
        with col3:
            quantity = st.text_input(f"Quantity {i+1}", key=f"qty_{i}")
        with col4:
            notes = st.text_input(f"Notes {i+1}", key=f"notes_{i}")
        item_details.append({
            'image': img_file,
            'name': name,
            'price': price,
            'quantity': quantity,
            'notes': notes
        })
    
    if st.button("Generate PDF"):
        with st.spinner("Generating PDF..."):
            try:
                # Generate the PDF object
                pdf = generate_pdf(item_details, header_text=col_header)
                
                # Save to a temporary buffer
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

