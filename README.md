#  Thermal Image SQL Database — Loyola LS Campus

This repository contains the SQLite database used to store thermal image data collected from windows on Loyola’s Lakeshore campus.

The database consists of two relational tables: `static` and `environment_logs`.

---

##  Table: `static`

This table stores **static information** about each window, such as its location in a building.

### Columns:

- **`location_id`** (TEXT)  
  Primary key used to connect the `static` and `environment_logs` tables.  
  - **Format**: First letter in each word in the building name (lowercase) / Floor number / Window position from the left  
  - **Example**: `ch_1_2` → Cuneo Hall, first floor, third window from the left

- **`building_name`** (TEXT)  
  Name of the building in lowercase with underscores replacing spaces.  
  - **Example**: `cuneo_hall`

- **`floor_number`** (INTEGER)  
  The floor where the window is located.  
  - **Format**: `0` for basement, `1` for first floor, and so on  
  - **Example**: `1` (first floor)

- **`side_of_building`** (TEXT)  
  Cardinal direction indicating which side of the building the window is on.  
  - **Format**: All lowercase  
  - **Example**: `north`

---

##  Table: `environment_logs`

This table stores **dynamic environmental readings** linked to each window.

### Columns:

- **`log_id`** (INTEGER)  
  Auto-incremented unique ID for each log entry.  
  - **Example**: `12`

- **`location_id`** (TEXT)  
  Foreign key referencing the `static` table.  
  - **Example**: `ch_1_2` (same as in `static`)

- **`outside_temp`** (REAL)  
  Outside temperature at the time of the reading in °F.  
  - **Example**: `45.2`

- **`min_temp`** (REAL)  
  Minimum temperature recorded on the window.  
  - **Example**: `63.1`

- **`max_temp`** (REAL)  
  Maximum temperature recorded on the window.  
  - **Example**: `71.8`

- **`time_taken_hours`** (INTEGER)  
  Hour of the day when the reading was taken (0–23).  
  - **Example**: `3` → Data collected between 3:00 AM – 3:59 AM  
  - **Example**: `23` → Data collected between 11:00 PM – 11:59 PM

- **`windows_opened`** (TEXT)  
  Indicates whether the window was opened during the logging period.  
  - **Format**: `'Y'` for yes, `'N'` for no  
  - **Example**: `N`

- **`date`** (TEXT)  
  Date when the reading was taken.  
  - **Format**: `YYYY-MM-DD`  
  - **Example**: `2025-03-30`

- **`url`** (TEXT)  
  Link to the corresponding thermal image in Google Drive.  
  - **Example**: `https://example.com/images/ch_1_2_2025-03-30.jpg`
