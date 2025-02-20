## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Samskriti-Foundation/upanishads-scripts
   ```

2. **Navigate to the project directory:**

   ```bash
   cd upanishads-scripts
   ```

3. **Install dependencies using a Virtual Environment:**

   a. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

   b. Activate the virtual environment:

   - **Linux/macOS:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows:**
     ```bash
      venv\Scripts\activate
     ```

   c. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

1. Ensure that the required csv files and audio files are in place
data/isha.csv, data/ken01.csv,  data/kena02.csv etc.
2. Ensure that the following .env parameters are correct for the next step

CSV_INS='isha|data/isha.csv|0,kena|data/kena01.csv|1'  # name|filepath|chapter,name|filepath|chapter
CSV_UPANISHADS="data/upanishads.csv"
UPANISHADS="isha/ishopanishad,kena/kenopanishad" 

3. (Optional) If not already done - consolidate the per-upanishad-per-chapter csv files into one file and add columns for upanishad name and chapter.
Except isha (only chapter 0), other upanishads will have chapters

```bash
python reformat_csv.py
```
## Run the backend server (see upanishads-backend/README.MD for step-by-step instructions)

4. Start the server using FastAPI CLI:

```bash
fastapi dev
```

5. Populate the upanishads database

```bash
python populate_db.py
```
