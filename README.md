This is the repository containing the SQL database for thermal images taken on Loyola's LS campus.

There are two tables, static and environment_logs. 

static contains the static information of the windows.

  location_ID is the primary key for connecting the two tables. TEXT
    Format: First letter in each word in building name lowercase / Floor Number (1 is first floor above basement, basement is 0) / Window position from the left (start at 0)
    Example: "ch_1_2", Cuneo Hall, first floor, third window from the left.

  building_name is the building name. TEXT
    Format: all lowercase with underscores for spaces
    Example: "cuneo_hall"

  floor_number is the floor where the window is located. INTEGER
    Format: Basement is 0 and each row of windows will increase by 1
    Example: "1", first floor

  side_of_building is the side of the building the window is located. TEXT
    Format: All lowercase, consult image guide for help with which side is which, cardinal directions.
            # Need to make image guide as well as consider alternatives
    Example: "north", North side of building



environment_logs contains the dynamic environmental readings associated with each window.

log_id is the unique identifier for each observation. INTEGER
  Format: Auto-incremented integer assigned to each row automatically
  Example: "12", the 12th entry in the logs

location_id is the foreign key linking each log to a window in the static table. TEXT
  Format: Must match an existing location_id in the static table
  Example: "ch_1_2", refers to the same window described in static

outside_temp is the temperature outside at the time of the reading. REAL
  Format: Decimal temperature in degrees Fahrenheit
  Example: "45.2", 45.2°F outside

min_temp is the minimum temperature recorded on the window. REAL
  Format: Decimal temperature in degrees Fahrenheit
  Example: "63.1", 63.1°F at coldest point on the window

max_temp is the maximum temperature recorded on the window. REAL
  Format: Decimal temperature in degrees Fahrenheit
  Example: "71.8", 71.8°F at warmest point on the window

time_taken_hours is the length of time (in hours) over which the reading was taken rounded down. INTEGER
  Format: Whole number, 0-23 for a full day
  Example: "3", data collected at 3:00 am - 3:59am. "23", data collected at 11:00 pm - 11:59 pm

windows_opened indicates whether the window was opened during the logging period. TEXT
  Format: 'Y' for yes, 'N' for no
    Example: "N", the window remained closed

date is the date when the reading was taken. TEXT
  Format: YYYY-MM-DD
  Example: "2025-03-30", March 30, 2025

url is a link to the corresponding thermal image in a google drive. TEXT
  Format: Valid URL string pointing to image or file location
  Example: "https://example.com/images/ch_1_2_2025-03-30.jpg"


















    
  
