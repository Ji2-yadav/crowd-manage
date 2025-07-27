## **Project Drishti: Simulation API**

This document defines the data models and API endpoints for the Project Drishti simulation server. The server manages the event state in memory, and all interactions from the UI, agent tools, or a demo controller are performed via these endpoints.

-----

## **Data Models**

### Zone Object

Describes the properties of a specific area within the event venue.

```json
"hall_1_lower": {
    "area_sqm": 5000,
    "num_people": 4900,
    "density_sqm_per_person": 1.02,
    "bottleneck_risk": "critical" | "high" | "medium" | "low",
    "active_alerts": ["AlertType", ...]
}
```

### Personnel Object

Describes a single medical or security staff member.

```json
"med_01": {
    "name": "Priya Singh",
    "type": "medical" | "security",
    "status": "PersonnelStatus",
    "current_zone": "<zone_id>"
}
```

### Gate Object

Describes a single gate or exit.

```json
"e1_fire_exit": {
    "zone_id": "<zone_id>",
    "status": "GateStatus",
    "type": "GateType"
}
```

### Enumerations

  * **`AlertType`**: A list of strings representing possible crisis events.

      * `"Overcrowding"`
      * `"MedicalEmergency"`
      * `"Fire"`
      * `"SecurityThreat"`
      * `"Stampede"`

  * **`PersonnelStatus`**: The current availability of a staff member.

      * `"available"`
      * `"dispatched"`

  * **`GateStatus`**: The current state of a gate.

      * `"open"`
      * `"closed"`

  * **`GateType`**: The type or purpose of a gate.

      * `"main_gate"`
      * `"emergency_exit"`
      * `"fire_exit"`
      * `"service_exit"`

-----

## **API Endpoints**

### Get Full Simulation State

  * **Method & Path**: `GET /state`
  * **Description**: Retrieves the complete, real-time state of the simulation. This is intended for polling by a UI or dashboard.
  * **Request Body**: None.
  * **Success Response (`200 OK`)**: A JSON object containing the top-level `zones`, `personnel`, and `gates` objects.

### Trigger a Live Event

  * **Method & Path**: `POST /event`
  * **Description**: Allows a presenter to manually trigger a critical event in a specific zone.
  * **Request Body**:
    ```json
    {
        "type": "AlertType",
        "zone": "<zone_id>"
    }
    ```
  * **Success Response (`200 OK`)**:
    ```json
    { "status": "success", "message": "Stampede event triggered in hall_1_lower" }
    ```
  * **Error Response (`400 Bad Request`)**:
    ```json
    { "status": "error", "message": "Invalid zone_id or event type provided." }
    ```

### Toggle a Gate

  * **Method & Path**: `POST /actions/toggle-gate`
  * **Description**: Action tool endpoint to open or close a specific gate.
  * **Request Body**:
    ```json
    {
        "gate_id": "<gate_id>",
        "status": "GateStatus"
    }
    ```
  * **Success Response (`200 OK`)**:
    ```json
    { "status": "success", "message": "Gate <gate_id> has been set to <status>" }
    ```

### Dispatch a Unit

  * **Method & Path**: `POST /actions/dispatch-unit`
  * **Description**: Action tool endpoint to dispatch a personnel unit.
  * **Request Body**:
    ```json
    {
        "personnel_id": "<personnel_id>",
        "destination_details": "string"
    }
    ```
  * **Success Response (`200 OK`)**:
    ```json
    { "status": "success", "message": "Unit <personnel_id> dispatched successfully" }
    ```

### Make an Announcement

  * **Method & Path**: `POST /actions/make-announcement`
  * **Description**: Action tool endpoint to log a public announcement request.
  * **Request Body**:
    ```json
    {
        "zone_id": "<zone_id>",
        "message": "string"
    }
    ```
  * **Success Response (`200 OK`)**:
    ```json
    { "status": "success", "message": "Announcement for <zone_id> acknowledged" }
    ```


### Evacuate Zone

  * **Endpoint**: `POST /actions/evacuate`
  * **Description**: Initiates a full evacuation protocol for a specified zone or the entire venue. On the backend, this should open all fire and emergency exits in the target zone(s) and begin rapidly decreasing the `num_people` count.
  * **Request Body**:
    ```json
    {
        "zone_id": "<zone_id>" | "all"
    }
    ```
  * **Success Response (`200 OK`)**:
    ```json
    {
        "status": "success",
        "message": "Evacuation protocol initiated for zone_id: hall_1_lower"
    }
    ```

### Activate Crowd Control Protocol

  * **Endpoint**: `POST /actions/activate-crowd-control-protocol`
  * **Description**: Triggers a pre-defined set of actions to mitigate dangerous overcrowding or a stampede. This is a step below a full evacuation. On the backend, this can open all non-main gates, reduce the rate of new people entering, and post an "Overcrowding" alert.
  * **Request Body**:
    ```json
    {
        "zone_id": "<zone_id>"
    }
    ```
  * **Success Response (`200 OK`)**:
    ```json
    {
        "status": "success",
        "message": "Crowd control protocol activated for zone_id: hall_1_lower"
    }
    ```