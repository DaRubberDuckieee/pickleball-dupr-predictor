import pickle
import m2cgen as m2c

# Load the model
with open('dupr_model.pkl', 'rb') as f:
    data = pickle.load(f)
    # Extract model from tuple if needed
    model = data[0] if isinstance(data, tuple) else data

# Convert to pure Python
python_code = m2c.export_to_python(model)

# Save to file
with open('api/model_code.py', 'w') as f:
    f.write("# Auto-generated model code - DO NOT EDIT\n")
    f.write("# This is a pure Python implementation of the Gradient Boosting model\n\n")
    f.write("def predict(input_vector):\n")
    f.write("    return " + python_code + "\n")

print("Model converted to pure Python successfully!")
print("File saved to: api/model_code.py")
