from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.Interface import Interface_Static

def generate_cube_step(output_path):
    # Create a 2x2x2 cube
    box = BRepPrimAPI_MakeBox(2.0, 2.0, 2.0).Shape()
    
    # Initialize STEP Writer
    writer = STEPControl_Writer()
    writer.Transfer(box, STEPControl_AsIs)
    
    # Save the file
    status = writer.Write(output_path)
    if status == 1:
        print(f"✅ Successfully generated: {output_path}")
    else:
        print("❌ Failed to write STEP file.")

if __name__ == "__main__":
    import os
    os.makedirs("tests/dummies", exist_ok=True)
    generate_cube_step("tests/dummies/cube.step")