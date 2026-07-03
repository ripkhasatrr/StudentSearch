from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import os

app = Flask(__name__)

# Load Excel data
df = pd.read_excel("roll_numbers.xlsx")

# Photos folder
PHOTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", result=None)

    # Get form values
    query = request.form.get("query", "").strip()
    sort_by = request.form.get("sort_by", "Name_ASC")
    gender = request.form.get("gender", "All")
    offset = int(request.form.get("offset", 0))

    # Start with all rows
    result_df = df.copy()

    # Apply search filter if query is provided
    if query:
        mask = (
            result_df["Name"].astype(str).str.contains(query, case=False, na=False) |
            result_df["RollNo"].astype(str).str.contains(query, case=False, na=False) |
            result_df["Contact"].astype(str).str.contains(query, case=False, na=False)
        )
        result_df = result_df[mask]
        
    # Apply Gender Filter
    if gender and gender != "All":
        result_df = result_df[result_df["Gender"].astype(str).str.strip().str.title() == gender.title()]
    
    # Safe Sorting (avoiding type comparison errors)
    if sort_by == "Name_ASC":
        result_df = result_df.sort_values(by="Name", key=lambda col: col.astype(str).str.lower(), ascending=True)
    elif sort_by == "Name_DESC":
        result_df = result_df.sort_values(by="Name", key=lambda col: col.astype(str).str.lower(), ascending=False)
    elif sort_by == "RollNo_ASC":
        result_df["_sort_roll"] = pd.to_numeric(result_df["RollNo"], errors="coerce")
        result_df = result_df.sort_values(by="_sort_roll", ascending=True)
    elif sort_by == "RollNo_DESC":
        result_df["_sort_roll"] = pd.to_numeric(result_df["RollNo"], errors="coerce")
        result_df = result_df.sort_values(by="_sort_roll", ascending=False)

    # Prevent mobile crash by limiting max results rendered at once
    total_results = len(result_df)
    limit = 60
    
    # slice the dataframe instead of just taking the head
    result_df = result_df.iloc[offset:offset+limit]

    if result_df.empty:
        result = None
    else:
        result = []
        for row in result_df.to_dict(orient="records"):
                roll = str(row["RollNo"]).strip()
                # Remove .0 if present
                if roll.endswith('.0'):
                    roll = roll[:-2]
                found = False
                for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
                    photo_path = os.path.join(PHOTO_DIR, f"{roll}{ext}")
                    if os.path.exists(photo_path):
                        row["photo_filename"] = f"{roll}{ext}"
                        found = True
                        break
                if not found:
                    row["photo_filename"] = None
                result.append(row)

    if request.form.get("ajax") == "1":
        return render_template("cards.html", result=result)
                
    return render_template("index.html", result=result, total_results=total_results, limit=limit, current_offset=offset)

@app.route("/photos/<filename>")
def photos(filename):
    return send_from_directory(PHOTO_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)
