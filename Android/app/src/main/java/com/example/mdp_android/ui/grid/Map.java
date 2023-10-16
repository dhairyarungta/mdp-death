package com.example.mdp_android.ui.grid;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.util.Log;
import android.view.DragEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Toast;
import android.os.Handler;


import androidx.annotation.Nullable;

import androidx.core.content.ContextCompat;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import com.example.mdp_android.R;
import com.example.mdp_android.controllers.RpiController;
import com.example.mdp_android.ui.home.HomeFragment;
import com.example.mdp_android.ui.home.HomeViewModel;

import java.util.ArrayList;
//import java.util.logging.Handler;


public class Map extends View {
    private static final String TAG = "MapController";
    private static final int NUM_COLS = 20, NUM_ROWS = 20;
    private static final float WALL_THICKNESS = 5;
    private static final String DEFAULT_DIRECTION = "N";
    private static boolean mapDrawn = false;
    private static Cell[][] cells;
    private static float cellSize;
    private Paint startPaint, obstacleFacePaint, obstaclePaint, robotPaint, exploredPaint, cellPaint, linePaint, whitePaint, targetTextPaint, imageIdentifiedPaint;

    private static int currentSelected = -1;
    private static ArrayList<Obstacle> obstacleCoor = new ArrayList<>();

    // robot start coordinates
    private static Robot robot = new Robot();
    private Bitmap robotDirectionBitmap;
    private static boolean canDrawRobot = false;
    private static boolean canSetDirection = false;
    private static boolean start = false;

    private static boolean taskType = false;

    public void setStart(boolean start) { this.start = start; }
    public void setCanSetDirection(boolean setDir) { canSetDirection = setDir; }
    public void setCanDrawRobot(boolean draw) {
        canDrawRobot = draw;
    }
    public void setTaskType(boolean task) { taskType = task; }
    public String getTaskType() {
        if (taskType) return "FASTEST_PATH";
        else return "EXPLORATION";
    }

    // initialize map
    public Map(Context context, @Nullable AttributeSet attributes) {
        super(context, attributes);

        // create objects
        startPaint = new Paint();
        obstacleFacePaint = new Paint();
        obstaclePaint = new Paint();
        robotPaint = new Paint();
        exploredPaint = new Paint();
        cellPaint = new Paint();
        linePaint = new Paint();
        whitePaint = new Paint();
        targetTextPaint = new Paint();
        imageIdentifiedPaint = new Paint();

        // TODO: use these paints
        // paint for paths
        startPaint.setColor(Color.GREEN);
        exploredPaint.setColor(Color.parseColor("#A4FEFF"));

        // paint for grid cells
        cellPaint.setColor(Color.WHITE);
        linePaint.setColor(ContextCompat.getColor(context, R.color.background));
        linePaint.setStrokeWidth(WALL_THICKNESS);
        linePaint.setStyle(Paint.Style.FILL_AND_STROKE);

        // paint for robot
        robotPaint.setColor(Color.parseColor("#C8A2C8"));

        // paint for obstacle
        obstaclePaint.setColor(Color.BLACK);
        obstacleFacePaint.setColor(Color.RED);
        whitePaint.setColor(Color.WHITE);
        whitePaint.setStyle(Paint.Style.FILL_AND_STROKE);
        whitePaint.setTextSize(11);

        // paint for images
        targetTextPaint.setColor(Color.WHITE);
        targetTextPaint.setStyle(Paint.Style.FILL_AND_STROKE);
        targetTextPaint.setFakeBoldText(true);
        targetTextPaint.setTextSize(16);
        targetTextPaint.setTextAlign(Paint.Align.CENTER);
        imageIdentifiedPaint.setColor(Color.parseColor("#89B09F"));

    }

    // Grid Cell object
    private class Cell {
        float sX, sY, eX, eY;
        String type;
        String id = "-1";
        int obsIndex = -1;
        Paint paint;
        public Cell(float startX, float startY, float endX, float endY, String type, Paint paint) {
            this.sX = startX;
            this.sY = startY;
            this.eX = endX;
            this.eY = endY;
            this.type = type;
            this.paint = paint;

        }

        public String getId() { return id; }
        public void setId(String id) { this.id = id; }

        public String getType() {
            return this.type;
        }

        public int getObsIndex() {
            return obsIndex;
        }

        public void setObsIndex(int index) {
            this.obsIndex = index;
        }

        public void setType(String type) {
            this.type = type;
            switch (type) {
                case "image":
                    this.paint = imageIdentifiedPaint;
                    break;
                case "obstacle":
                    this.paint = obstaclePaint;
                    break;
                case "robot":
                    this.paint = robotPaint;
                    break;
                case "start":
                    this.paint = startPaint;
                    break;
                case "unexplored":
                    this.paint = cellPaint;
                    break;
                case "explored":
                    this.paint = exploredPaint;
                    break;
            }
        }
     }

    // obstacle object
    public class Obstacle {
        // coordinates of position
        public int x, y, obsID, targetID;
        public String direction = DEFAULT_DIRECTION;
        public Obstacle(int x, int y) {
            this.x = x;
            this.y = y;
        }

        public Obstacle(int x, int y, int obsID) {
            this.x = x;
            this.y = y;
            this.obsID = obsID;
            this.targetID = -1;
        }

        public int getObsID() {
            return this.obsID;
        }

        public int getObsXCoor() {
            return this.x;
        }

        public void setObsXCoor(int x) {
            this.x = x;
        }

        public int getObsYCoor() {
            return this.y;
        }

        public void setObsYCoor(int y) {
            this.y = y;
        }

        public int getTargetID() {
            return this.targetID;
        }

        public void setTargetID(int targetID) {
            this.targetID = targetID;
        }

        public String getDirection() {
            return this.direction;
        }

        public void setDirection(String d) {
            this.direction = d;
        }

    }

    public static class Robot {
        public int x, y;
        public String direction = "N";

        public Robot() {
            Log.d(TAG, "creating robot");
            this.x = -1;
            this.y = -1;
        }
        public Robot(int x, int y) {
            this.x = x;
            this.y = y;
        }

        public int getX() {
            return this.x;
        }

        public int getY() {
            return this.y;
        }

        public String getDirection() {
            return this.direction;
        }

        public void setX(int x) {
            this.x = x;
        }

        public void setY(int y) {
            this.y = y;
        }

        public void setDirection(String d) {
            this.direction = d;
        }
    }

    private void createCell() {
        log("create cells");
        cells = new Cell[NUM_COLS + 1][NUM_ROWS + 1];
        this.cellSize = calculateCellSize();

        for (int x = 0; x <= NUM_COLS; x++)
            for (int y = 0; y <= NUM_ROWS; y++)
                cells[x][y] = new Cell(
                        x * cellSize + (cellSize / 30),
                        y * cellSize + (cellSize / 30),
                        (x + 1) * cellSize,
                        (y + 1) * cellSize,
                        "unexplored",
                        cellPaint);
    }

    private float calculateCellSize() {
        return (getWidth() / (NUM_COLS + 1));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        log("start drawing map");
        super.onDraw(canvas);
//        canvas.drawColor(Color.WHITE);
        if (!mapDrawn) {
            this.createCell();
            mapDrawn = true;
        }

        if (NUM_COLS == 0 || NUM_ROWS == 0) return;
        drawGrids(canvas);
        drawGridNumbers(canvas);
        drawObstacle(canvas);
        if (robot.getX() != -1 && robot.getY() != -1) drawRobot(canvas);
        drawIdentifiedImage(canvas);
        log("map drawn successfully");

    }

    private void drawGrids(Canvas canvas) {
        for (int x = 1; x <= NUM_COLS; x++)
            for (int y = 0; y < NUM_ROWS; y++) {
                canvas.drawRect(cells[x][y].sX, cells[x][y].sY, cells[x][y].eX, cells[x][y].eY, cells[x][y].paint);
            }
//                if (!cells[x][y].type.equals("image") && cells[x][y].getId().equals("-1")) {
//                    canvas.drawRect(cells[x][y].sX, cells[x][y].sY, cells[x][y].eX, cells[x][y].eY, cells[x][y].paint);
//                    canvas.drawText(y + "", x * cellSize + cellSize/2.5f, y * cellSize + cellSize/1.5f, blackPaint);
//                } else {
//                    canvas.drawRect(cells[x][y].sX, cells[x][y].sY, cells[x][y].eX, cells[x][y].eY, cells[x][y].paint);
//                    canvas.drawText(y + "", x * cellSize + cellSize/2.5f, y * cellSize + cellSize/1.5f, blackPaint);
//                }

        // draw vertical lines
        for (int c=0; c<=NUM_COLS; c++) {
            canvas.drawLine(cells[c][0].sX - (cellSize / 30) + cellSize, cells[c][0].sY - (cellSize / 30),
                    cells[c][0].sX - (cellSize / 30) + cellSize, cells[c][NUM_ROWS-1].eY + (cellSize / 30), linePaint);
        }

        // draw horizontal lines
        for (int r=0; r<=NUM_ROWS; r++) {
            canvas.drawLine(
                    cells[1][r].sX, cells[1][r].sY - (cellSize / 30),
                    cells[NUM_COLS][r].eX, cells[NUM_COLS][r].sY - (cellSize / 30), linePaint);
        }
    }

    private void drawGridNumbers(Canvas canvas) {
        for (int x = 1; x <= NUM_COLS; x++) {
            if (x > 9)
                canvas.drawText(Integer.toString(x - 1), cells[x][NUM_ROWS].sX + (cellSize / 5), cells[x][NUM_ROWS].sY + (cellSize / 2), whitePaint);
            else
                canvas.drawText(Integer.toString(x - 1), cells[x][NUM_ROWS].sX + (cellSize / 3), cells[x][NUM_ROWS].sY + (cellSize / 2), whitePaint);
        }
        for (int y = 0; y < NUM_ROWS; y++) {
            if ((this.convertRow(y)) > 10)
                canvas.drawText(Integer.toString(19 - y), cells[0][y].sX + (cellSize / 4), cells[0][y].sY + (cellSize / 1.5f), whitePaint);
            else
                canvas.drawText(Integer.toString(19 - y), cells[0][y].sX + (cellSize / 2f), cells[0][y].sY + (cellSize / 1.5f), whitePaint);
        }
    }

    private void drawObstacle(Canvas canvas) {
        log("drawing obstacles on map");
        RectF rect = null;
        if (obstacleCoor.size() > 0) {
            for (int i = 0; i < obstacleCoor.size(); i++) {
                int col = obstacleCoor.get(i).getObsXCoor();
                int row = this.convertRow(obstacleCoor.get(i).getObsYCoor());
                int obsID = obstacleCoor.get(i).getObsID();
                String direction = obstacleCoor.get(i).getDirection();
                rect = new RectF(col * cellSize, row * cellSize, (col + 1) * cellSize, (row + 1) * cellSize);
                canvas.drawRect(rect, obstaclePaint);
                canvas.drawText(obsID + "", col * cellSize + cellSize/2.5f, row * cellSize + cellSize/1.5f, whitePaint);
                // draw direction
                drawDirection(canvas, col, row, direction);
            }
        }
    }

    private void drawDirection(Canvas canvas, int col, int row, String direction) {
        float left = col * cellSize;
        float top = row * cellSize;
        float right = (col + 1) * cellSize;
        float bottom = (row + 1) * cellSize;
        float dWidth = 0.1f;
        switch (direction) {
            case "N":
                canvas.drawRect(left, top, right, (row+dWidth) * cellSize, obstacleFacePaint);
                break;
            case "S":
                canvas.drawRect(left, (row + 1 - dWidth) * cellSize, right, bottom, obstacleFacePaint);
                break;
            case "E":
                canvas.drawRect((col + 1 - dWidth) * cellSize, top, right, bottom, obstacleFacePaint);
                break;
            case "W":
                canvas.drawRect(left, top, (col + dWidth) * cellSize, bottom, obstacleFacePaint);
                break;
        }
    }

    private void drawIdentifiedImage(Canvas canvas) {
        log("drawing identified target ids on map");
        RectF rect = null;
        if (obstacleCoor.size() > 0) {
            for (int i = 0; i < obstacleCoor.size(); i++) {
                int col = obstacleCoor.get(i).getObsXCoor();
                int row = this.convertRow(obstacleCoor.get(i).getObsYCoor());
                int targetID = obstacleCoor.get(i).getTargetID();
                if (targetID != -1) {
                    String direction = obstacleCoor.get(i).getDirection();
                    rect = new RectF(col * cellSize, row * cellSize, (col + 1) * cellSize, (row + 1) * cellSize);
                    canvas.drawRect(rect, cells[col][row].paint);
                    canvas.drawText(targetID + "", col * cellSize + cellSize / 2f, row * cellSize + cellSize / 1.4f, targetTextPaint);
                    // draw direction
                    drawDirection(canvas, col, row, direction);
                }
            }
        }
    }

    private void drawRobot(Canvas canvas) {
        log("drawing robot on map");
        RectF rect;
        int col = robot.getX();
        int row = this.convertRow(robot.getY());
        rect = new RectF(col * cellSize, row * cellSize , (col + 1) * cellSize, (row + 1) * cellSize);
        switch (robot.getDirection()) {
                case "N":
                    robotDirectionBitmap = BitmapFactory.decodeResource(getResources(), R.drawable.robot_north);
                    break;
                case "E":
                    robotDirectionBitmap = BitmapFactory.decodeResource(getResources(), R.drawable.robot_east);
                    break;
                case "S":
                    robotDirectionBitmap = BitmapFactory.decodeResource(getResources(), R.drawable.robot_south);
                    break;
                case "W":
                    robotDirectionBitmap = BitmapFactory.decodeResource(getResources(), R.drawable.robot_west);
                    break;
                default:
                    break;
            }
//            cells[col][row].setType("robot");
//            canvas.drawRect(rect, robotPaint);
//            setRobotCoor(col, row, "N");
            canvas.drawBitmap(robotDirectionBitmap, null, rect, null);
    }

    public void setRobotCoor(int x, int y, String d) {
        log("setting robot coordinates: (" +x +y+")");
        int oldX = robot.getX();
        int oldY = this.convertRow(robot.getY());

        if (oldX != -1 && oldY != -1) {
            for (int i = oldX - 1; i <= oldX + 1; i++)
                for (int j = oldY - 1; j <= oldY + 1; j++)
                    if (!start) {
                        cells[i][j].setType("unexplored");
                    } else {
                        cells[i][j].setType("explored");
                    }
        }

        robot.setX(x);
        robot.setY(y);
        robot.setDirection(d);
        int col = x;
        int row = this.convertRow(y);
        for (int i = col - 1; i <= col + 1; i++)
            for (int j = row - 1; j <= row + 1; j++)
                if (isWithinCanvasRegion(i,j)) cells[i][j].setType("robot");


        this.invalidate();
    }


    // checks if the cell is occupied
    private boolean checkGridEmpty(int x, int y) {
//        if (cells[x][y].getType() != "robot" && cells[x][y].getType() != "obstacle") return true;
//        else return false;
        if (isWithinCanvasRegion(x, y)) {
            if (cells[x][y].getType() == "robot" || cells[x][y].getType() == "obstacle") return false;
            else return true;
        } else return true;
    }

    // checks if there is sufficient space to place a robot
    private boolean checkSpaceEnough(int x, int y) {
        for (int i = x - 1; i <= x + 1; i++)
            for (int j = y - 1; j <= y + 1; j++)
                if (cells[i][j].getType() == "obstacle") {
                    Toast.makeText(getContext(), "cell is already occupied", Toast.LENGTH_SHORT).show();
                    return false;
                }
        return true;
    }


    public boolean onDragEvent(DragEvent event) {
        switch (event.getAction()) {
            case DragEvent.ACTION_DROP:
                Log.d(TAG, "drop object here");
                // Determine the coordinates of the drop event
                float x = event.getX();
                float y = event.getY();

                // Convert the coordinates into grid cell coordinates
                int cellX = (int) (x / cellSize);  // Calculate cell width
                int cellY = this.convertRow((int) (y / cellSize));  // Calculate cell height

                // Check if the drop is within the bounds of your 20x20 grid
                if (isWithinCanvasRegion(cellX, cellY) && checkGridEmpty(cellX, this.convertRow(cellY))) {
                    // handle drop event (place obstacle in grid cell)
                    String obsID = event.getClipData().getItemAt(0).getText().toString();
                    setObstacleCoor(cellX, cellY, obsID);
                    // ADDED: send to RPI obstacle details
//                    RpiController.sendToRpi(RpiController.getObstacleDetails(obstacleCoor.get(obstacleCoor.size() - 1)));
                    HomeFragment.modifyObstacleVisibility(Integer.parseInt(obsID)-1, false);
                    this.invalidate();
                } else {
                    log("out of boundary");
                }
                break;
            default:
                break;
        }
        return true;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float x = event.getX();
        float y = event.getY();

        int cellX = (int) (x / cellSize);  // Calculate cell width
        int cellY = (int) (y / cellSize);  // Calculate cell height

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                // initiate the drag operation
                if (isWithinCanvasRegion(cellX, cellY)) {
                    if (canSetDirection) {
                        String d;
                        if (cells[cellX][cellY].getType() == "obstacle") {
                            d = getNewDirection(obstacleCoor.get(cells[cellX][cellY].getObsIndex()).getDirection());
                            obstacleCoor.get(cells[cellX][cellY].getObsIndex()).setDirection(d);
                            // ADDED: send to RPI obstacle details
//                            RpiController.sendToRpi(RpiController.getObstacleDetails(obstacleCoor.get(cells[cellX][cellY].getObsIndex())));
                            this.invalidate();
                        } else if (cells[cellX][cellY].getType() == "robot") {
                            d = getNewDirection(robot.getDirection());
                            robot.setDirection(d);
                            // ADDED: send to RPI robot details
//                            RpiController.sendToRpi(RpiController.getRobotDetails(robot));
                            sendRobotStatus();
                            this.invalidate();
                        }
                    }
                    else if (canDrawRobot) {
                        // draw robot at touched position
                        log("draw robot");
                        if (checkSpaceEnough(cellX, cellY)) {
                            setRobotCoor(cellX, this.convertRow(cellY), DEFAULT_DIRECTION);
                            // ADDED: send to RPI robot details
//                            RpiController.sendToRpi(RpiController.getRobotDetails(robot));
                            sendRobotStatus();
//                            this.invalidate();
                        } else {
                            log("already have an object here");
                        }
                    } else if (cells[cellX][cellY].getType() == "obstacle") {
                        currentSelected = cells[cellX][cellY].getObsIndex();
                        log("current selected: " + currentSelected);
                        int oldX = obstacleCoor.get(currentSelected).getObsXCoor();
                        int oldY = this.convertRow(obstacleCoor.get(currentSelected).getObsYCoor());
                        cells[oldX][oldY].setType("unexplored");
                        cells[oldX][oldY].setObsIndex(-1);
                        this.invalidate();
                    }
                }
                    break;
                case MotionEvent.ACTION_MOVE:
                    // Update the position of the dragged TextView
                    if (!(currentSelected == -1) && checkGridEmpty(cellX, cellY)) {
//                        if (isWithinCanvasRegion(cellX, cellY) && checkGridEmpty(cellX, cellY)) {
//                        if (!(currentSelected == -1)) {
                            log("within boundary, can move");
                            obstacleCoor.get(currentSelected).setObsXCoor(cellX);
                            obstacleCoor.get(currentSelected).setObsYCoor(this.convertRow(cellY));
                            this.invalidate();
//                        }
//                        } else {
//                            log("out of boundary");
//                            HomeFragment.modifyObstacleVisibility(currentSelected, true);
//                        }
                    }
                    break;
                case MotionEvent.ACTION_UP:
                    // Handle drop
                    log("ACTION_UP: ("+cellX + " , "+cellY+")");
                    if (isWithinCanvasRegion(cellX, cellY) && checkGridEmpty(cellX, cellY)) {
                        if (!(currentSelected == -1)) {
                            // ADDED: send to RPI obstacle details
//                            RpiController.sendToRpi(RpiController.getObstacleDetails(obstacleCoor.get(currentSelected)));
                            cells[cellX][cellY].setObsIndex(currentSelected);
                            cells[cellX][cellY].setType("obstacle");
                            currentSelected = -1;
                            this.invalidate();
                        }
                    } else {
                        log("out of boundary");
                        if (!(currentSelected == -1)) {
                            HomeFragment.modifyObstacleVisibility(obstacleCoor.get(currentSelected).getObsID() - 1, true);
                            obstacleCoor.remove(currentSelected);
                            updateObstacleCoor(currentSelected);
                            currentSelected = -1;
                        }
                    }
                    break;
            }
        return true;
    }

    public boolean isWithinCanvasRegion(int x, int y) {
        // check if (x, y) falls within specific bounds of the canvas
        if (x >= 1 && x <= NUM_COLS && y >= 0 && y < NUM_ROWS) return true;
        else return false;
    }

    private void setObstacleCoor(int x, int y, String obsID) {
        log("Setting new obstacle coordinates");
        Obstacle obstacle = new Obstacle(x, y, Integer.parseInt(obsID));
        Map.obstacleCoor.add(obstacle);
        int row = this.convertRow(y);
        cells[x][row].setObsIndex(obstacleCoor.size()-1);
        cells[x][row].setType("obstacle");
    }

    private String getNewDirection(String currentDir) {
        switch(currentDir) {
            case "N":
                return "E";
            case "E":
                return "S";
            case "S":
                return "W";
            case "W":
                return "N";
        }
        return "N";
    }

    private void log(String message) {
        Log.d(TAG, message);
    }

    private int convertRow(int r) {return NUM_ROWS - r;}

    // uncomment on actual
    public void clearGrid() {
        // clear obstacles
        obstacleCoor.clear();
        currentSelected = -1;

        // reset robot
        robot.setX(-1);
        robot.setY(-1);

        // clear grids
        for (int x = 1; x <= NUM_COLS; x++) {
            for (int y = 0; y < NUM_ROWS; y++) {
                if (!cells[x][y].type.equals("unexplored")) {
                    cells[x][y].setType("unexplored");
                }
                if (cells[x][y].getObsIndex() != -1) {
                    cells[x][y].setObsIndex(-1);
                }
            }
        }

        this.invalidate();
    }

    // clear grid: test
//    public void clearGrid() {
//        // clear obstacles
//        currentSelected = -1;
//
//        // clear grids
//        for (int x = 1; x <= NUM_COLS; x++) {
//            for (int y = 0; y < NUM_ROWS; y++) {
//                if (cells[x][y].type.equals("explored")) {
//                    cells[x][y].setType("unexplored");
//                }
//            }
//        }
//
//        this.invalidate();
//    }

    private void updateObstacleCoor(int start) {
        int x, y, index;
        log("updating obstacle arraylist...");
        for (int i=start; i<obstacleCoor.size();i++) {
            x = obstacleCoor.get(i).getObsXCoor();
            y = this.convertRow(obstacleCoor.get(i).getObsYCoor());
            index = cells[x][y].getObsIndex();
            cells[x][y].setObsIndex(index - 1);
        }
    }

    public void sendMapToRpi() {
        String task = this.getTaskType();
        RpiController.sendToRpi(RpiController.getMapDetails(task, robot, obstacleCoor));
    }

    public void setObsTargetID(int obsID, int imgID) {
        log("updating identified image id to obstacle");
        for (int i=0;i<obstacleCoor.size();i++) {
            if (obstacleCoor.get(i).getObsID() == obsID) {
                obstacleCoor.get(i).setTargetID(imgID);
                int x = obstacleCoor.get(i).getObsXCoor();
                int y = this.convertRow(obstacleCoor.get(i).getObsYCoor());
                log("initial cell type: "+cells[x][y].getType());
                cells[x][y].setType("image");
                log("updated cell type: "+cells[x][y].getType());
                this.invalidate();
                return;
            }
        }
    }

    public Obstacle getObstacle(int obsID) {
        for (int i=0;i<obstacleCoor.size();i++) {
            if (obstacleCoor.get(i).getObsID() == obsID) {
                return obstacleCoor.get(i);
            }
        }
        return null;
    }

    public boolean robotInMap() {
        return robot.getX() != -1 && robot.getY() != -1;
    }

    private void sendRobotStatus() {
        String x = Integer.toString(robot.getX()-1);
        String y = Integer.toString(robot.getY()-1);
        String status = "robot at (" + x + " , " + y + ") facing " + robot.getDirection();
        Log.d(TAG, "status: "+ status);
        Intent intent = new Intent("getStatus");
        intent.putExtra("robot", status);
        LocalBroadcastManager.getInstance(getContext()).sendBroadcast(intent);
    }

    public void setExploredPath(ArrayList<ArrayList<Integer>> path) {
        final int delayMillis = 3000;
        final Handler handler = new Handler();
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                // Do something after 5s = 5000ms
                for (int i = 0; i < path.size(); i++) {
                    int row = convertRow(path.get(i).get(1) + 1);
                    int col = path.get(i).get(0) + 1;
                    if (cells[col][row].getType() == "unexplored") {
                        cells[col][row].setType("explored");
                        invalidate();
                    }

                    // send status
                    String status = "robot at (" + path.get(i).get(0) + " , " + path.get(i).get(1) + ")";
                    Log.d(TAG, "status: " + status);
                    Intent intent = new Intent("getStatus");
                    intent.putExtra("robot", status);
                    LocalBroadcastManager.getInstance(getContext()).sendBroadcast(intent);
                }
            }
        }, delayMillis);
    }

    // TODO: update robot movements on map for manual navigation (only if robot in map)
    public void moveForward() {
        String currentDir = robot.getDirection();
        switch (currentDir) {
            case "N":
                log("N");
                break;
            case "S":
                log("S");
                break;
            case "E":
                log("E");
                break;
            case "W":
                log("W");
                break;
        }
    }

    public void turnLeft() {
        String currentDir = robot.getDirection();
        switch (currentDir) {
            case "N":
                log("N");
                break;
            case "S":
                log("S");
                break;
            case "E":
                log("E");
                break;
            case "W":
                log("W");
                break;
        }
    }

    public void turnRight() {
        String currentDir = robot.getDirection();
        switch (currentDir) {
            case "N":
                log("N");
                break;
            case "S":
                log("S");
                break;
            case "E":
                log("E");
                break;
            case "W":
                log("W");
                break;
        }
    }

    public void moveBack() {
        String currentDir = robot.getDirection();
        switch (currentDir) {
            case "N":
                log("N");
                break;
            case "S":
                log("S");
                break;
            case "E":
                log("E");
                break;
            case "W":
                log("W");
                break;
        }
    }

}
