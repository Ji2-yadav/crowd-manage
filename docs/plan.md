### Tools

#### Action
- send_alert(person_id, zone_id) - all commanders in zone or just single person
    - commanders
    - medical personnels
    - security
- make_announcement(text, zone_id)
- toggle_gate(gate_id)
- dispatch_drone(zone_id)
- dispatch_medical_personnel(personnel_id)
- request_items(stall_id, items: str)

#### Get
- get_zone_state(zone_id)
- get_food_stall_state(food_stall_id)
- get_medical_personnels(zone_id)
- get_security_personnels(security)
- get_crowd_optimizations(zone_id)
- get_crowd_density(zone_id)
- get_gates(zone_id)
- get_zones()
- get_map(zone_id)
- get_food_stalls(zone_id)
    - get in a nice format - like ascii - with paths and gateids labelled.

---

### Func (excluding from the tools)

- find_person(img_person)
    - direct dashboard
- get_best_path(loc1, loc2)

## In
- send_message_to_agent(commander_id, text)
- analyse_video()
    - fire
    - medical
    - crowd-agitation
- sensor_alert_to_agent(alert_type)
    - audio levels high
    - smoke sensor
- 



----

### Notes
- this could be a multi agent setup - but the tools and functions will have to be implemented. im not sure if i should implement sub-agent as a function right now or implement the tools/functions itself.
- 

----

### V1
Get env ready for use of vertex agent thing
#### Tools
- 

#### Functions
- analyse_video_feed()
    - should find bool
        - fire
        - person collapsing
        - person bleeding
    - calculate people density
    - get a heatmap of people
- create_map()
- get_map()
- make_announcement()
- send_alert()
- get_zone_state(zone_id)
- get_medical_personnels(zone_id)
- get_security_personnels(security)
- get_crowd_optimizations(zone_id)
- get_crowd_flow(zone_id)
- get_crowd_density(zone_id)
- predict_crowd_agitation(zone_id)
- get_stampede_probability(zone_id)
- send_message_to_agent(from:str, msg:str)

