package com.example.mdp_android.controllers;

import android.os.Handler;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import com.example.mdp_android.ui.grid.Map;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class RpiController {
    private static final String TAG = "RPI messages";
    private static BluetoothController bController = BluetoothControllerSingleton.getInstance(new Handler());

    /**
     * read messages received from rpi and pass it to JSON object
     * @param received
     */

    public static String getRpiMessageTyoe(String received) {
//        try {
//            JSONObject jsonObj = new JSONObject(received);
//            if (jsonObj.get("type").equals("COORDINATES")) {
//                return "robot";
//            } else if (jsonObj.get("type").equals("IMAGE_RESULTS")) {
//                return "image";
//            } else {
//                return "";
//            }
//        } catch (Exception e) {
//            Log.e(TAG, "Failed to pass json: " + e);
//        }
        if (received.contains("COORDINATES")) {
            return "robot";
        } else if (received.contains("IMAGE_RESULTS")) {
            return "image";
        } else {
            return "";
        }
    }

    public static JSONObject readRpiMessages(String received) {
        try {
            JSONObject jsonObj = new JSONObject(received);
            if (jsonObj.get("type").equals("COORDINATES")) {
                // get current coordinates of robot from rpi
                JSONObject robot = jsonObj.getJSONObject("data").getJSONObject("robot");
                return robot;
            } else if (jsonObj.get("type").equals("IMAGE_RESULTS")) {
                // get image rec results from rpi
                JSONObject results = jsonObj.getJSONObject("data");
                return results;
            }

        } catch (Exception e) {
            Log.e(TAG, "Failed to pass json: ", e);
        }
        return null;
    }

    public static String getRobotStatus (JSONObject robot) {
        String status = "";
        try {
            String x = robot.get("x").toString();
            String y = robot.get("y").toString();
            String d = robot.get("dir").toString();
            status = "robot at (" + x + " , " + y + ") facing " + d;
            Log.d(TAG, "robot current status: "+status);
        } catch (Exception e) {
            Log.d(TAG, "failed to parse json: "+e);
        }
        return status;
    }


    // TODO: see how get obstacle coordinates
    public static String getTargetStatus(JSONObject results) {
        String status = "";
        try {
            String obsId = results.get("obs_id").toString();
            String imgId = results.get("img_id").toString();
            status = obsId + " -> " + imgId;
        } catch (Exception e) {
            Log.d(TAG, "failed to parse json: "+e);
        }
        return status;
    }

    // get map details into json (including task type)
    public static JSONObject getMapDetails(String task, Map.Robot robot, ArrayList<Map.Obstacle> obstacles) {
        JSONObject message = new JSONObject();
        JSONObject data = new JSONObject();
        JSONArray obstaclesCoor = new JSONArray();
        try {
            data.put("task", task);
            data.put("robot", getRobotDetails(robot));
            for (Map.Obstacle i : obstacles) {
                obstaclesCoor.put(getObstacleDetails(i));
            }
            data.put("obstacles", obstaclesCoor);
            message.put("type", "START_TASK");
            message.put("data", data);

        } catch (Exception e) {
            Log.d(TAG, "Failed to parse string into json: ", e);
        }
        return message;
    }

    // TODO: change after checklist complete
    public static JSONObject getRobotDetails(Map.Robot robot) {
        JSONObject checklistPayload = new JSONObject();
        JSONObject robotCoor = new JSONObject();
        try {
            robotCoor.put("id", "R");
            robotCoor.put("x", robot.getX() - 1);
            robotCoor.put("y", robot.getY() - 1);
            robotCoor.put("dir", robot.getDirection());
            checklistPayload.put("robot", robotCoor);
        } catch (Exception e) {
            Log.d(TAG, "Failed to parse string into json: ", e);
        }
//        return robotCoor;
        return checklistPayload;
    }

    // TODO: change after checklist complete
    public static JSONObject getObstacleDetails(Map.Obstacle obstacle) {
        JSONObject checklistPayload = new JSONObject();
        JSONObject obstacleCoor = new JSONObject();
        try {
            obstacleCoor.put("id", obstacle.getObsID());
            obstacleCoor.put("x", obstacle.getObsXCoor() - 1);
            obstacleCoor.put("y", obstacle.getObsYCoor() - 1);
            obstacleCoor.put("dir", obstacle.getDirection());
            checklistPayload.put("obstacle", obstacleCoor);
        } catch (Exception e) {
            Log.d(TAG, "Failed to parse string into json: ", e);
        }
//        return obstacleCoor;
        return checklistPayload;
    }

    // get navigation details into json (up, down, left, right buttons)
    public static JSONObject getNavDetails(List<String> commands) {
        JSONObject message = new JSONObject();
        JSONObject commandsJson = new JSONObject();
        try {
            commandsJson.put("commands", commands);
            Log.d(TAG, "commands: "+commands);
            message.put("type","NAVIGATION");
            message.put("data", commandsJson);

        } catch (Exception e) {
            Log.d(TAG, "Failed to parse string into json: ", e);
        }
        return message;
    }

    // function to send messages to rpi
    public static void sendToRpi(JSONObject jsonObj) {
        try {
            bController.write(jsonObj.toString().getBytes(StandardCharsets.UTF_8));
            Log.d(TAG, "sendToRPi: \n" + jsonObj.toString(2));
        } catch (Exception e) {
            Log.e(TAG, "Failed to send message to rpi: ", e);
        }
    }

    // checklist
    public static void sendToRpi2(String jsonObj) {
        try {
            bController.write(jsonObj.getBytes(StandardCharsets.UTF_8));
//            Log.d(TAG, "sendToRPi: \n" + jsonObj.toString(2));
        } catch (Exception e) {
            Log.e(TAG, "Failed to send message to rpi: ", e);
        }
    }
}
