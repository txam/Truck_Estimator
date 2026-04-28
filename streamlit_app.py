import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Truck Estimator", layout="wide")

st.title("Truck Requirement & Fuel Estimator")
st.write("Estimate the number of trucks required to keep the excavator working and calculate fuel efficiency in L/BCM.")

# -----------------------------
# INPUTS
# -----------------------------

st.sidebar.header("Loading parameters")

truck_capacity = st.sidebar.slider(
    "Truck capacity (BCM)",
    min_value=10,
    max_value=120,
    value=38,
    step=1
)

loading_time = st.sidebar.slider(
    "Loading time per truck (min)",
    min_value=1.0,
    max_value=15.0,
    value=2.0,
    step=0.1
)

st.sidebar.header("Haulage parameters")

haul_distance = st.sidebar.slider(
    "One-way haul distance (m)",
    min_value=100,
    max_value=5000,
    value=1000,
    step=100
)

loaded_speed = st.sidebar.slider(
    "Loaded speed (km/h)",
    min_value=5,
    max_value=50,
    value=30,
    step=1
)

empty_speed = st.sidebar.slider(
    "Empty speed (km/h)",
    min_value=5,
    max_value=60,
    value=30,
    step=1
)

dumping_time = st.sidebar.slider(
    "Dumping time (min)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5
)

spotting_time = st.sidebar.slider(
    "Spotting / manoeuvre time (min)",
    min_value=0.0,
    max_value=10.0,
    value=1.0,
    step=0.5
)

st.sidebar.header("Fuel parameters")

truck_fuel_lph = st.sidebar.slider(
    "Truck fuel consumption (L/h per truck)",
    min_value=20,
    max_value=100,
    value=50,
    step=2
)

excavator_fuel_lph = st.sidebar.slider(
    "Excavator fuel consumption (L/h)",
    min_value=30,
    max_value=300,
    value=224,
    step=2
)

fuel_target = st.sidebar.slider(
    "Fuel target (L/BCM)",
    min_value=0.20,
    max_value=2.00,
    value=0.60,
    step=0.05
)

bulldozer_fuel_lph = st.sidebar.slider("Bulldozer fuel (L/h)", 30, 80, 50, 5)

# -----------------------------
# CALCULATIONS
# -----------------------------

loaded_haul_time = (haul_distance / 1000) / loaded_speed * 60
empty_return_time = (haul_distance / 1000) / empty_speed * 60

truck_cycle_time = (
    loading_time
    + loaded_haul_time
    + dumping_time
    + empty_return_time
    + spotting_time
)

required_trucks = truck_cycle_time / loading_time
recommended_trucks = math.ceil(required_trucks)

excavator_max_prod = (truck_capacity / loading_time) * 60
production_bcm_h = min(
    (truck_capacity * recommended_trucks / truck_cycle_time) * 60,
    excavator_max_prod
)
total_truck_fuel = recommended_trucks * truck_fuel_lph

total_fuel_lph = total_truck_fuel + excavator_fuel_lph + bulldozer_fuel_lph

fuel_l_bcm = total_fuel_lph / production_bcm_h

match_factor = (recommended_trucks * loading_time) / truck_cycle_time




# -----------------------------
# OPTIMIZATION CURVE (L/BCM vs trucks)
# -----------------------------

truck_range = range(1, 21)  # puedes ajustar el rango (1–20 camiones)

results = []

for n in truck_range:
    # Producción para n camiones
    production_raw = (truck_capacity * n / truck_cycle_time) * 60
    production = (truck_capacity * n / truck_cycle_time) * 60
    production = min(production_raw, excavator_max_prod)

    total_fuel = (n * truck_fuel_lph) + excavator_fuel_lph + bulldozer_fuel_lph

    if production > 0:
        l_bcm = total_fuel / production
    else:
        l_bcm = None

    # Consumo total
    total_fuel = (n * truck_fuel_lph) + excavator_fuel_lph + bulldozer_fuel_lph

    # Evitar división por cero
    if production > 0:
        l_bcm = total_fuel / production
    else:
        l_bcm = None

    results.append({
        "Trucks": n,
        "L/BCM": l_bcm
    })

df = pd.DataFrame(results)

# Encontrar el óptimo (mínimo L/BCM)
optimal_row = df.loc[df["L/BCM"].idxmin()]
optimal_trucks = int(optimal_row["Trucks"])
optimal_l_bcm = optimal_row["L/BCM"]


# -----------------------------
# RESULTS
# -----------------------------

st.subheader("Main results")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cycle time", f"{truck_cycle_time:.1f} min")
col2.metric("Required trucks", f"{required_trucks:.1f}")
col3.metric("Recommended trucks", recommended_trucks)
col4.metric("Match factor", f"{match_factor:.2f}")

st.subheader("Production and fuel")

col5, col6, col7, col8 = st.columns(4)

col5.metric("Production", f"{production_bcm_h:.0f} BCM/h")
col6.metric("Total fuel", f"{total_fuel_lph:.0f} L/h")
col7.metric("Fuel efficiency", f"{fuel_l_bcm:.2f} L/BCM")
col8.metric("Fuel target", f"{fuel_target:.2f} L/BCM")

if fuel_l_bcm <= fuel_target:
    st.success("Fuel efficiency is within target.")
else:
    st.warning("Fuel efficiency is above target.")

st.subheader("Optimal fleet")

col_opt1, col_opt2 = st.columns(2)

col_opt1.metric("Optimal trucks (min L/BCM)", optimal_trucks)
col_opt2.metric("Minimum L/BCM", f"{optimal_l_bcm:.2f}")

st.subheader("Fuel efficiency vs number of trucks")

st.line_chart(df.set_index("Trucks"))

st.write(f"Current selection: **{recommended_trucks} trucks → {fuel_l_bcm:.2f} L/BCM**")

if recommended_trucks == optimal_trucks:
    st.success("You are operating at optimal fuel efficiency.")
elif recommended_trucks < optimal_trucks:
    st.warning("You may improve efficiency by adding trucks.")
else:
    st.warning("You may be over-trucking (excess trucks).")

# -----------------------------
# BREAKDOWN
# -----------------------------

st.subheader("Fuel breakdown")

st.write(f"Truck fuel: **{total_truck_fuel:.0f} L/h** ({recommended_trucks} trucks)")
st.write(f"Excavator fuel: **{excavator_fuel_lph:.0f} L/h**")
st.write(f"Bulldozer fuel: **{bulldozer_fuel_lph:.0f} L/h**")
st.write(f"Total system fuel: **{total_fuel_lph:.0f} L/h**")

# -----------------------------
# INTERPRETATION
# -----------------------------

st.subheader("Interpretation")

if match_factor < 0.95:
    st.error("Excavator may wait → add trucks or reduce cycle time")
elif match_factor <= 1.10:
    st.success("Balanced fleet")
else:
    st.warning("Truck queue likely → possible inefficiency")

st.write("Fuel efficiency includes trucks + excavator + bulldozer.")