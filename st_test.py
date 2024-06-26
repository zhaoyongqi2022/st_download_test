import streamlit as st
import scenariogeneration as sg
import scenariogeneration.xosc as xosc
import xml.etree.ElementTree as ET
from xml.dom import minidom
from io import BytesIO
import zipfile

# Define the Scenario class as provided
class Scenario(sg.ScenarioGenerator):
    def __init__(self, id):
        super().__init__()
        self.open_scenario_version = 2
        self.id = id

    def scenario(self, **kwargs):
        ### create catalogs
        catalog = xosc.Catalog()
        catalog.add_catalog("VehicleCatalog", "../xosc/Catalogs/Vehicles")

        ### create road
        road = xosc.RoadNetwork(
            roadfile="../xodr/e6mini.xodr", scenegraph="../models/e6mini.osgb"
        )

        ### create parameters
        paramdec = xosc.ParameterDeclarations()

        ### create vehicles
        bb = xosc.BoundingBox(2, 5, 1.8, 2.0, 0, 0.9)
        fa = xosc.Axle(0.523598775598, 0.8, 1.68, 2.98, 0.4)
        ba = xosc.Axle(0.523598775598, 0.8, 1.68, 0, 0.4)
        white_veh = xosc.Vehicle(
            "car_white", xosc.VehicleCategory.car, bb, fa, ba, 69, 10, 10
        )

        white_veh.add_property_file("../models/car_white.osgb")
        white_veh.add_property("model_id", "0")

        bb = xosc.BoundingBox(1.8, 4.5, 1.5, 1.3, 0, 0.8)
        fa = xosc.Axle(0.523598775598, 0.8, 1.68, 2.98, 0.4)
        ba = xosc.Axle(0.523598775598, 0.8, 1.68, 0, 0.4)
        red_veh = xosc.Vehicle(
            "car_red", xosc.VehicleCategory.car, bb, fa, ba, 69, 10, 10
        )

        red_veh.add_property_file("../models/car_red.osgb")
        red_veh.add_property("model_id", "2")

        ## create entities
        egoname = "Ego"
        targetname = "Target"

        entities = xosc.Entities()
        entities.add_scenario_object(egoname, white_veh)
        entities.add_scenario_object(targetname, red_veh)

        ### create init
        init = xosc.Init()
        step_time = xosc.TransitionDynamics(
            xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 1
        )

        egospeed = xosc.AbsoluteSpeedAction(3, step_time)
        egostart = xosc.TeleportAction(xosc.LanePosition(25, 0, -3, 0))

        targetspeed = xosc.AbsoluteSpeedAction(15, step_time)
        targetstart = xosc.TeleportAction(xosc.RelativeRoadPosition(30, 0, egoname))

        init.add_init_action(egoname, egospeed)
        init.add_init_action(egoname, egostart)
        init.add_init_action(targetname, targetspeed)
        init.add_init_action(targetname, targetstart)

        ### create an event for target
        trigcond = xosc.AccelerationCondition(2.9, xosc.Rule.greaterThan)
        trigger = xosc.EntityTrigger(
            "mytesttrigger", 0.2, xosc.ConditionEdge.none, trigcond, egoname
        )

        event = xosc.Event("myfirstevent", xosc.Priority.overwrite)
        event.add_trigger(trigger)

        sin_time = xosc.TransitionDynamics(
            xosc.DynamicsShapes.linear, xosc.DynamicsDimension.time, 3.9
        )
        action = xosc.AbsoluteSpeedAction(0, sin_time)
        event.add_action("newspeed", action)

        ## create the maneuver
        man = xosc.Maneuver("my_maneuver")
        man.add_event(event)

        mangr = xosc.ManeuverGroup("mangroup")
        mangr.add_actor(targetname)
        mangr.add_maneuver(man)

        ### create an event for the ego
        start_trig = xosc.ValueTrigger(
            "ego_acc",
            0,
            xosc.ConditionEdge.none,
            xosc.SimulationTimeCondition(0.5, xosc.Rule.greaterThan),
        )
        start_action = xosc.AbsoluteSpeedAction(
            30,
            xosc.TransitionDynamics(
                xosc.DynamicsShapes.sinusoidal, xosc.DynamicsDimension.rate, 3
            ),
        )

        ego_start_event = xosc.Event("startevent", xosc.Priority.overwrite)
        ego_start_event.add_trigger(start_trig)
        ego_start_event.add_action("start_action", start_action)

        trigcond = xosc.StandStillCondition(0.5)
        standstill_trigger = xosc.EntityTrigger(
            "standstill trigger", 0.1, xosc.ConditionEdge.none, trigcond, targetname
        )
        stop_action = xosc.AbsoluteSpeedAction(
            0,
            xosc.TransitionDynamics(
                xosc.DynamicsShapes.linear, xosc.DynamicsDimension.rate, 10
            ),
        )

        ego_event = xosc.Event("stopevent", xosc.Priority.overwrite)
        ego_event.add_trigger(standstill_trigger)
        ego_event.add_action("stop_action", stop_action)

        ego_man = xosc.Maneuver("ego_maneuver")
        ego_man.add_event(ego_start_event)
        ego_man.add_event(ego_event)

        ego_mangr = xosc.ManeuverGroup("mangroup")
        ego_mangr.add_actor(egoname)
        ego_mangr.add_maneuver(ego_man)

        starttrigger = xosc.ValueTrigger(
            "starttrigger",
            0,
            xosc.ConditionEdge.rising,
            xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan),
        )
        act = xosc.Act("my_act", starttrigger)
        act.add_maneuver_group(mangr)
        act.add_maneuver_group(ego_mangr)

        ## create the storyboard
        sb = xosc.StoryBoard(
            init,
            xosc.ValueTrigger(
                "stop_simulation",
                0,
                xosc.ConditionEdge.rising,
                xosc.SimulationTimeCondition(15, xosc.Rule.greaterThan),
                "stop",
            ),
        )
        sb.add_act(act)

        ## create the scenario
        sce = xosc.Scenario(
            f"adapt_speed_example_{self.id}",
            "Mandolin",
            paramdec,
            entities=entities,
            storyboard=sb,
            roadnetwork=road,
            catalog=catalog,
            osc_minor_version=self.open_scenario_version,
        )
        return sce

# Streamlit app code
st.title("OpenSCENARIO File Generator")

# Number of scenarios to generate
num_scenarios = 10

# Create a BytesIO buffer for the ZIP file
zip_buffer = BytesIO()

# Create a ZIP file
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    for i in range(num_scenarios):
        # Generate the scenario
        scenario = Scenario(id=i)
        xosc_scenario = scenario.scenario()

        # Convert the scenario to XML
        root_element = xosc_scenario.get_element()
        xml_string = ET.tostring(root_element, encoding='unicode', method='xml')

        # Prettify the XML string
        dom = minidom.parseString(xml_string)
        pretty_xml_string = dom.toprettyxml()

        # Add the XML file to the ZIP
        zf.writestr(f"scenario_{i}.xosc", pretty_xml_string)

# Move the pointer to the beginning of the BytesIO buffer
zip_buffer.seek(0)

# Create a download button
st.download_button(
    label="Download OpenSCENARIO files",
    data=zip_buffer,
    file_name="scenarios.zip",
    mime="application/zip"
)

st.write("Click the button above to download the OpenSCENARIO files.")
