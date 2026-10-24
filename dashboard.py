import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date, timedelta
from streamlit_autorefresh import st_autorefresh
from live_camera import open_camera, read_camera_frame, close_camera


from parking.parking_manager import ParkingManager
from parking.database import ParkingDatabase
from parking.space_mapper import map_vehicles_to_spaces
from vehicle_detection import detect_vehicles


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="AI Smart Parking Management System",
    page_icon="🚗",
    layout="wide",
)

TOTAL_SPACES = 9

# --------------------------------------------------
# INITIALIZE DATABASE AND PARKING MANAGER
# --------------------------------------------------
database = ParkingDatabase()

if "manager" not in st.session_state:
    manager = ParkingManager(3, 3)
    for space in database.get_occupied_spaces():
        row, col = divmod(space - 1, 3)
        manager.vehicle_entered(row, col)
    st.session_state.manager = manager

manager = st.session_state.manager


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------
st.title("🚗 AI Smart Parking Management System")
st.caption("Parking occupancy, vehicle events, reports, and AI image analysis.")

if "notice" in st.session_state:
    st.info(st.session_state.notice)
    del st.session_state.notice


# --------------------------------------------------
# PARKING OVERVIEW
# --------------------------------------------------
st.subheader("📊 Parking Overview")

capacity = manager.get_total_capacity()
occupied_count = manager.get_occupied_spaces()
available_count = manager.get_available_spaces()
occupancy_pct = (occupied_count / capacity * 100) if capacity else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Capacity", capacity)
c2.metric("Occupied Spaces", occupied_count)
c3.metric("Available Spaces", available_count)
c4.metric("Occupancy", f"{occupancy_pct:.1f}%")
c5.metric("Vehicles Parked", manager.get_current_vehicles())
st.progress(min(max(occupancy_pct / 100, 0.0), 1.0))
st.divider()


# --------------------------------------------------
# MAIN PARKING SPACE LAYOUT
# --------------------------------------------------
st.subheader("🅿️ Parking Space Layout")
st.caption("Current saved parking status; numbering is row-wise.")

matrix = manager.get_matrix()
for row_index, row in enumerate(matrix):
    cols = st.columns(3)
    for col_index, is_occupied in enumerate(row):
        space = row_index * 3 + col_index + 1
        with cols[col_index]:
            if is_occupied:
                st.error(f"🚙 SPACE {space}\n\nOCCUPIED")
            else:
                st.success(f"🅿️ SPACE {space}\n\nAVAILABLE")
st.divider()


# --------------------------------------------------
# MANUAL VEHICLE ENTRY AND EXIT
# --------------------------------------------------
st.subheader("🚘 Manual Vehicle Entry and Exit")
left, right = st.columns(2)

with left:
    st.markdown("### Vehicle Entry")
    available_spaces = [
        r * 3 + c + 1
        for r, row in enumerate(manager.get_matrix())
        for c, is_occupied in enumerate(row)
        if not is_occupied
    ]
    if available_spaces:
        entry_space = st.selectbox(
            "Select an available parking space",
            available_spaces,
            key="entry_space",
        )
        if st.button("Park Vehicle", use_container_width=True):
            row, col = divmod(entry_space - 1, 3)
            if manager.vehicle_entered(row, col):
                database.record_event("ENTRY", entry_space)
                st.session_state.notice = f"Vehicle parked in Space {entry_space}."
            else:
                st.session_state.notice = f"Could not park in Space {entry_space}."
            st.rerun()
    else:
        st.warning("Parking is full. No spaces are available.")

with right:
    st.markdown("### Vehicle Exit")
    occupied_spaces_manual = [
        r * 3 + c + 1
        for r, row in enumerate(manager.get_matrix())
        for c, is_occupied in enumerate(row)
        if is_occupied
    ]
    if occupied_spaces_manual:
        exit_space = st.selectbox(
            "Select an occupied parking space",
            occupied_spaces_manual,
            key="exit_space",
        )
        if st.button("Remove Vehicle", use_container_width=True):
            row, col = divmod(exit_space - 1, 3)
            if manager.vehicle_exited(row, col):
                database.record_event("EXIT", exit_space)
                st.session_state.notice = f"Vehicle exited from Space {exit_space}."
            else:
                st.session_state.notice = f"Could not remove vehicle from Space {exit_space}."
            st.rerun()
    else:
        st.info("No vehicles are currently parked.")
st.divider()


# --------------------------------------------------
# SESSION AND DATABASE STATISTICS
# --------------------------------------------------
st.subheader("📈 Session Statistics")
a, b, c = st.columns(3)
a.metric("Session Entries", manager.get_total_entries())
b.metric("Session Exits", manager.get_total_exits())
c.metric("Parking Full", "Yes" if manager.is_full() else "No")

stats = database.get_statistics()
st.subheader("🗄️ All-Time Database Statistics")
d1, d2, d3 = st.columns(3)
d1.metric("Recorded Entry Events", stats["total_entries"])
d2.metric("Recorded Exit Events", stats["total_exits"])
d3.metric("Net Recorded Events", stats["net_entries"])
st.caption("Event totals count historical records; they are not necessarily the same as current occupancy.")
st.divider()


# --------------------------------------------------
# ANALYTICS AND REPORTS
# --------------------------------------------------
st.header("📊 Parking Analytics and Reports")

today = date.today()
default_start = today - timedelta(days=6)
date_col1, date_col2 = st.columns(2)
with date_col1:
    report_start = st.date_input(
        "Report start date",
        value=default_start,
        key="report_start_date",
    )
with date_col2:
    report_end = st.date_input(
        "Report end date",
        value=today,
        key="report_end_date",
    )

if report_start > report_end:
    st.error("Start date must be on or before end date.")
    report_df = pd.DataFrame(columns=["Record ID", "Event", "Space", "Date and Time"])
else:
    all_history = database.get_history(limit=100000)
    report_df = pd.DataFrame(
        all_history,
        columns=["Record ID", "Event", "Space", "Date and Time"],
    )
    if not report_df.empty:
        # Database timestamps are stored as ISO-8601 strings with the
        # machine's local UTC offset. Extract the calendar date written in
        # each timestamp before filtering, rather than converting it to UTC.
        # UTC conversion can move an event to the previous/next date and make
        # the daily analytics disagree with the history table.
        from datetime import datetime

        def parse_event_date(value):
            try:
                return datetime.fromisoformat(str(value)).date()
            except (TypeError, ValueError):
                return None

        report_df["Report Date"] = report_df["Date and Time"].apply(
            parse_event_date
        )
        report_df = report_df[
            report_df["Report Date"].notna()
            & (report_df["Report Date"] >= report_start)
            & (report_df["Report Date"] <= report_end)
        ].copy()
        report_df["Report Date"] = pd.to_datetime(report_df["Report Date"])

valid_report = report_start <= report_end
if valid_report:
    entries_in_range = int((report_df["Event"] == "ENTRY").sum()) if not report_df.empty else 0
    exits_in_range = int((report_df["Event"] == "EXIT").sum()) if not report_df.empty else 0

    st.caption(
        "These counts include only ENTRY/EXIT events whose stored calendar date "
        "falls within the selected range. All-Time Database Statistics above "
        "include the full history. Reapplying AI occupancy records only spaces "
        "whose occupied/vacant state changes; unchanged spaces do not create events."
    )
    r1, r2, r3 = st.columns(3)
    r1.metric("Entries in Period", entries_in_range)
    r2.metric("Exits in Period", exits_in_range)
    r3.metric("Total Events in Period", len(report_df))

    # Build a complete daily series, including zero-event days.
    days = pd.date_range(report_start, report_end, freq="D")
    daily = pd.DataFrame({"Date": days})
    if not report_df.empty:
        daily_counts = (
            report_df.groupby(["Report Date", "Event"])
            .size()
            .unstack(fill_value=0)
        )
        daily_counts.index = pd.to_datetime(daily_counts.index).normalize()
        daily = daily.set_index("Date").join(daily_counts, how="left").fillna(0).reset_index()
    else:
        daily["ENTRY"] = 0
        daily["EXIT"] = 0

    for event_name in ("ENTRY", "EXIT"):
        if event_name not in daily.columns:
            daily[event_name] = 0
        daily[event_name] = daily[event_name].astype(int)

    st.subheader("Daily Vehicle Entry and Exit Events")
    chart_df = daily.rename(columns={"Date": "Day", "ENTRY": "Entries", "EXIT": "Exits"})
    st.bar_chart(chart_df.set_index("Day")[["Entries", "Exits"]])

    st.subheader("Events by Parking Space")
    if report_df.empty:
        st.info("No events were recorded during the selected date range.")
    else:
        by_space = (
            report_df.groupby(["Space", "Event"])
            .size()
            .unstack(fill_value=0)
            .reindex(range(1, TOTAL_SPACES + 1), fill_value=0)
        )
        for event_name in ("ENTRY", "EXIT"):
            if event_name not in by_space.columns:
                by_space[event_name] = 0
        st.bar_chart(by_space[["ENTRY", "EXIT"]])

    if not report_df.empty:
        export_df = report_df[["Record ID", "Event", "Space", "Date and Time"]].copy()
    else:
        export_df = pd.DataFrame(columns=["Record ID", "Event", "Space", "Date and Time"])

    st.download_button(
        "Download selected-period report (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=f"parking_report_{report_start}_{report_end}.csv",
        mime="text/csv",
        disabled=not valid_report,
    )
st.divider()


# --------------------------------------------------
# PARKING HISTORY
# --------------------------------------------------
st.subheader("📋 Recent Parking History")
history = database.get_history(limit=20)
if history:
    history_data = [
        {
            "Record ID": row[0],
            "Event": row[1],
            "Space": row[2],
            "Date and Time": row[3],
        }
        for row in history
    ]
    st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
else:
    st.info("No parking history has been recorded yet.")
st.divider()


# --------------------------------------------------
# AI VEHICLE DETECTION AND SPACE MAPPING
# --------------------------------------------------
st.header("🤖 AI Vehicle Detection and Parking Occupancy")
st.write(
    "Upload a parking-lot image to detect supported vehicles and estimate "
    "which of the nine  parking spaces are occupied."
)

uploaded_image = st.file_uploader(
    "Upload parking image",
    type=["jpg", "jpeg", "png"],
    key="ai_parking_image",
)
confidence = st.slider(
    "Detection Confidence",
    min_value=0.10,
    max_value=0.90,
    value=0.35,
    step=0.05,
    key="ai_confidence",
)

if uploaded_image is not None:
    try:
        image = Image.open(uploaded_image).convert("RGB")
        st.image(image, caption="Uploaded Parking Image", use_container_width=True)

        if st.button("Detect Vehicles and Map Spaces", type="primary"):
            with st.spinner("Detecting vehicles and mapping parking spaces..."):
                image_width, image_height = image.size
                annotated_image, detections, vehicle_count = detect_vehicles(
                    image_path=image,
                    confidence=confidence,
                )
                mapped_vehicles, ai_occupied_spaces = map_vehicles_to_spaces(
                    detections, image_width, image_height
                )
                st.session_state["ai_mapped_vehicles"] = mapped_vehicles
                st.session_state["ai_occupied_spaces"] = ai_occupied_spaces
                st.session_state["ai_annotated_image"] = annotated_image
                st.session_state["ai_vehicle_count"] = vehicle_count
                st.session_state["ai_image_size"] = (image_width, image_height)
                st.session_state["ai_apply_confirmed"] = False

        if "ai_mapped_vehicles" in st.session_state:
            mapped_vehicles = st.session_state["ai_mapped_vehicles"]
            ai_occupied_spaces = st.session_state["ai_occupied_spaces"]
            annotated_image = st.session_state["ai_annotated_image"]
            vehicle_count = st.session_state["ai_vehicle_count"]
            image_width, image_height = st.session_state["ai_image_size"]

            st.subheader("Detection Results")
            st.image(
                annotated_image[:, :, ::-1].copy(),
                caption="YOLO Vehicle Detections",
                use_container_width=True,
            )
            m1, m2 = st.columns(2)
            m1.metric("YOLO Vehicle Detections", vehicle_count)
            m2.metric("Vehicles Mapped to Parking Spaces", len(mapped_vehicles))

            if mapped_vehicles:
                st.dataframe(
                    pd.DataFrame(mapped_vehicles),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.warning("No supported vehicles were mapped to parking spaces.")

            st.subheader("🅿️ AI Parking Occupancy Preview")
            ai_available_spaces = [
                space for space in range(1, 10)
                if space not in ai_occupied_spaces
            ]
            p1, p2, p3 = st.columns(3)
            p1.metric("Estimated Occupied", len(ai_occupied_spaces))
            p2.metric("Estimated Available", len(ai_available_spaces))
            p3.metric("Total Spaces", 9)

            for row_index in range(3):
                cols = st.columns(3)
                for col_index in range(3):
                    space = row_index * 3 + col_index + 1
                    with cols[col_index]:
                        if space in ai_occupied_spaces:
                            st.error(f"🚙 SPACE {space}\n\nOCCUPIED")
                        else:
                            st.success(f"🅿️ SPACE {space}\n\nAVAILABLE")

            st.caption(
                f"Image dimensions: {image_width} × {image_height}. "
                "AI preview does not change saved occupancy until confirmed."
            )
            st.warning(
                "Applying AI results replaces the current saved occupancy "
                "for all nine spaces. Check the preview first."
            )
            confirmed = st.checkbox(
                "I checked the AI preview and want to update saved occupancy.",
                key="ai_apply_confirmed",
            )

            if st.button(
                "Apply AI Occupancy to Dashboard and Database",
                disabled=not confirmed,
            ):
                updated_manager = ParkingManager(3, 3)
                for space in ai_occupied_spaces:
                    row, col = divmod(space - 1, 3)
                    updated_manager.vehicle_entered(row, col)

                old_occupied = set(database.get_occupied_spaces())
                new_occupied = set(ai_occupied_spaces)

                for space in sorted(old_occupied - new_occupied):
                    database.record_event("EXIT", space)
                for space in sorted(new_occupied - old_occupied):
                    database.record_event("ENTRY", space)

                st.session_state.manager = updated_manager
                for key in (
                    "ai_mapped_vehicles",
                    "ai_occupied_spaces",
                    "ai_annotated_image",
                    "ai_vehicle_count",
                    "ai_image_size",
                    "ai_apply_confirmed",
                ):
                    st.session_state.pop(key, None)

                st.session_state.notice = (
                    "Parking occupancy updated from the AI image. "
                    "Please verify the layout."
                )
                st.rerun()

    except Exception as error:
        st.error(f"Vehicle detection or mapping failed: {error}")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "AI Smart Parking Management System | YOLO vehicle detection with "
    "parking-space mapping. AI occupancy is previewed first and only saved "
    "after confirmation."
)

# --------------------------------------------------
# LIVE CAMERA
# --------------------------------------------------
st.header("📹 Live Camera Parking Monitor")

if "live_camera" not in st.session_state:
    st.session_state.live_camera = None

if "live_camera_running" not in st.session_state:
    st.session_state.live_camera_running = False

start_col, stop_col = st.columns(2)

with start_col:
    if st.button(
        "Start Live Camera",
        disabled=st.session_state.live_camera_running,
        key="start_live_camera",
    ):
        try:
            st.session_state.live_camera = open_camera()
            st.session_state.live_camera_running = True
            st.rerun()
        except Exception as error:
            st.error(f"Camera error: {error}")

with stop_col:
    if st.button(
        "Stop Live Camera",
        disabled=not st.session_state.live_camera_running,
        key="stop_live_camera",
    ):
        close_camera(st.session_state.live_camera)
        st.session_state.live_camera = None
        st.session_state.live_camera_running = False
        st.rerun()

if st.session_state.live_camera_running:
    camera_placeholder = st.empty()

    try:
        frame = read_camera_frame(st.session_state.live_camera)

        if frame is None:
            st.error("Unable to read a camera frame.")
        else:
            camera_placeholder.image(
                frame,
                caption="Live laptop camera",
                channels="RGB",
                use_container_width=True,
            )

        # Refresh the page periodically to capture another frame.
        st_autorefresh(
            interval=200,
            limit=None,
            key="live_camera_refresh",
        )

    except Exception as error:
        st.error(f"Live camera failed: {error}")
