package com.example.mdp_android.ui.home;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CompoundButton;
import android.widget.ImageButton;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;

import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProvider;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.RecyclerView;

import com.example.mdp_android.R;
import com.example.mdp_android.controllers.DeviceSingleton;
import com.example.mdp_android.controllers.RpiController;
import com.example.mdp_android.databinding.FragmentHomeBinding;
import com.example.mdp_android.ui.grid.Map;

import org.json.JSONObject;

import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.List;

public class HomeFragment extends Fragment {
    private static final String TAG = "HomeFragment";
    private static final int SPAN = 2;
    private FragmentHomeBinding binding;
    private HomeViewModel homeViewModel;
    private String connectedDevice = "";
    DeviceSingleton deviceSingleton;

    public Map map;

    private ImageButton up, down, left, right;
    private Button resetBtn, startBtn;
    private TextView robotStatus, targetStatus, bluetoothTextView, obsData;
    private RecyclerView obsList;
    private static RecyclerAdapter obsItems;
    private RecyclerView.LayoutManager layoutManager;
    private ToggleButton setRobot, setDirection, setTaskType;
    private Toast currentToast;


    @Override
    public View onCreateView(
            LayoutInflater inflater,
            ViewGroup container,
            Bundle savedInstanceState
    ) {
        homeViewModel = new ViewModelProvider(this).get(HomeViewModel.class);

        binding = FragmentHomeBinding.inflate(inflater, container, false);
        View root = binding.getRoot();

        bluetoothTextView = binding.textViewBluetooth;

        // register receiver for connected devices
        LocalBroadcastManager.getInstance(requireActivity()).registerReceiver(
                mNameReceiver,
                new IntentFilter("getConnectedDevice")
        );

        // register receiver for robot status
        LocalBroadcastManager.getInstance(requireActivity()).registerReceiver(
                mTextReceiver,
                new IntentFilter("getReceived")
        );

        LocalBroadcastManager.getInstance(requireActivity()).registerReceiver(
                initialStatusReceiver,
                new IntentFilter("getStatus")
        );


        return root;
    }

    // Update status whenever connection changes
    private BroadcastReceiver mNameReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String deviceName = intent.getStringExtra("name");
            if (deviceName.equals("")) {
                connectedDevice = "";
                deviceSingleton.setDeviceName(connectedDevice);
                updateBluetoothStatus();
            } else {
                connectedDevice = deviceName;
                deviceSingleton.setDeviceName(connectedDevice);
                Log.d(TAG, "onReceive: -msg- " + connectedDevice);
                updateBluetoothStatus();
            }
//            if (deviceName.equals("")) {
//                connectedDevice = "";
//                homeViewModel.setReceivedText(context.getString(
//                        R.string.bluetooth_device_connected_not));
//            } else {
//                connectedDevice = deviceName;
//                Log.d(TAG, "onReceive: -msg- " + connectedDevice);
//                homeViewModel.setReceivedText(context.getString(
//                        R.string.bluetooth_device_connected)+connectedDevice);
//            }
        }
    };

    // update robot coordinates whenever new coordinates are received
    private BroadcastReceiver mTextReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(TAG, "receiving messages");
            String status;
            String textReceived = intent.getStringExtra("received");
            JSONObject response = RpiController.readRpiMessages(textReceived);
            String messageType = RpiController.getRpiMessageTyoe(textReceived);
            if (messageType == "robot" ) {
                status = RpiController.getRobotStatus(response);
                homeViewModel.setRobotStatus(status);
                updateRobotPosition(response);
                // TODO: get robot coordinate message as list and update every few seconds using sleep and for loop
            } else if (messageType == "image") {
                status = RpiController.getTargetStatus(response);
                try {
                    Map.Obstacle o = map.getObstacle(Integer.parseInt(response.getString("obs_id")));
                    if (o != null) {
                        int x = o.getObsXCoor() - 1;
                        int y = o.getObsYCoor() - 1;
                        status = status + " at (" + x + ", " + y + ") facing " + o.getDirection();
                    } else {
                        status = "Invalid ID received";
                        toast("Invalid Obstacle ID received");
                    }
                } catch (Exception e) {
                    log("Failed to parse JSON: "+e);
                }
                homeViewModel.setTargetStatus(status);
                updateObstacle(response);
            }
        }
    };

    private BroadcastReceiver initialStatusReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String textReceived = intent.getStringExtra("robot");
            homeViewModel.setRobotStatus(textReceived);

        }
    };


    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        // remove receiver
        LocalBroadcastManager.getInstance(requireActivity()).unregisterReceiver(mNameReceiver);
        LocalBroadcastManager.getInstance(requireActivity()).unregisterReceiver(mTextReceiver);
        LocalBroadcastManager.getInstance(requireActivity()).unregisterReceiver(initialStatusReceiver);
    }

    @Override
    public void onViewCreated(View view, Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        // Robot control UI
        up = getView().findViewById(R.id.imageButton_up);
        down = getView().findViewById(R.id.imageButton_down);
        left = getView().findViewById(R.id.imageButton_left);
        right = getView().findViewById(R.id.imageButton_right);
        resetBtn = getView().findViewById(R.id.button_reset);
        robotStatus = getView().findViewById(R.id.textView_robotStatus);
        targetStatus = getView().findViewById(R.id.textView_targetCoor);
        obsData = getView().findViewById(R.id.textView_obsData);
        obsList = getView().findViewById(R.id.recyclerView_obsList);
        map = getView().findViewById(R.id.mapView);
        setRobot = getView().findViewById(R.id.button_startpoint);
        setDirection = getView().findViewById(R.id.button_setDirection);
        startBtn = getView().findViewById(R.id.button_start);
        setTaskType = getView().findViewById(R.id.button_taskType);

        createObstacleList();

        startBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                // sends task and robot and obstacles coordinates to rpi
                if (map.robotInMap()) {
                    map.sendMapToRpi();
                    map.setStart(true);
                    toast("Start Task: " + map.getTaskType());
                } else {
                    toast( "Map not filled");
                }
            }
        });

        resetBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                map.clearGrid();
                obsItems.setAllVisibility(true);
                map.setStart(false);
            }
        });

        up.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                toast("move forward");
                ArrayList<String> commands = new ArrayList<>();
                commands.add("SF050");
                RpiController.sendToRpi(RpiController.getNavDetails(commands));
            }
        });

        down.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                toast( "move backwards");
                ArrayList<String> commands = new ArrayList<>();
                commands.add("SB050");
                RpiController.sendToRpi(RpiController.getNavDetails(commands));
            }
        });

        left.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                toast( "turn left");
                ArrayList<String> commands = new ArrayList<>();
                commands.add("LF090");
//                commands.add("SF010");
                RpiController.sendToRpi(RpiController.getNavDetails(commands));
            }
        });

        right.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                toast("turn right");
                ArrayList<String> commands = new ArrayList<>();
                commands.add("RF090");
////                commands.add("SF010");
                RpiController.sendToRpi(RpiController.getNavDetails(commands));
            }
        });

        setRobot.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
                String message;
                if (b) {
                    message = "Select a cell to place robot";
                } else {
                    message = "Cancel";
                }
                toast(message);
                map.setCanDrawRobot(b);
                if (setDirection.isChecked()) setDirection.setChecked(!b);
            }
        });

        setDirection.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
                String message;
                if (b) {
                    message = "Select object to change direction";
                } else {
                    message = "cancel";
                }
                toast(message);
                map.setCanSetDirection(b);
                if (setRobot.isChecked()) setRobot.setChecked(!b);
            }
        });

        setTaskType.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
                String message;
                if (b) {
                    message = "Task type: Fastest Car";
                } else {
                    message = "Task type: Image Recognition";
                }
                toast(message);
                // set task type in map
                map.setTaskType(b);
            }
        });

    }

    // hydrating the view with the view model
    @Override
    public void onResume() {
        super.onResume();

        bluetoothTextView.setText(homeViewModel.getReceivedText().getValue());

        homeViewModel.getReceivedText().observe(getViewLifecycleOwner(), new Observer<String>() {
            @Override
            public void onChanged(@Nullable String s) {
                bluetoothTextView.setText(s);
            }
        });

        robotStatus.setText(homeViewModel.getRobotStatus().getValue());
        homeViewModel.getRobotStatus().observe(getViewLifecycleOwner(), new Observer<String>() {
            @Override
            public void onChanged(String s) {
                robotStatus.setText(s);
            }
        });

        targetStatus.setText(homeViewModel.getTargetStatus().getValue());
        homeViewModel.getTargetStatus().observe(getViewLifecycleOwner(), new Observer<String>() {
            @Override
            public void onChanged(String s) {
                targetStatus.setText(s);
            }
        });
    }


    public void createObstacleList() {
        obsItems = new RecyclerAdapter(new String[]{"1", "2", "3", "4", "5", "6", "7", "8"});
        obsList.setAdapter(obsItems);
        layoutManager = new GridLayoutManager(getContext(), SPAN);
        obsList.setLayoutManager(layoutManager);

    }

    public void updateBluetoothStatus() {
        log("updating bluetooth status in home fragment...");
        deviceSingleton = DeviceSingleton.getInstance();

        if (!deviceSingleton.getDeviceName().equals("")) {
            connectedDevice = deviceSingleton.getDeviceName();
            homeViewModel.setReceivedText(getContext().getString(
                    R.string.bluetooth_device_connected)+connectedDevice);

        } else {
            homeViewModel.setReceivedText(getContext().getString(
                    R.string.bluetooth_device_connected_not));
        }
    }

    public void updateRobotPosition(JSONObject robot) {
        try {
            int x = Integer.parseInt(robot.getString("x"));
            int y = Integer.parseInt(robot.getString("y"));
            String d = robot.getString("dir");
            if (map.isWithinCanvasRegion(x+1, y+1)) {
                map.setRobotCoor(x + 1, y + 1, d);
            } else {
                toast( "Invalid coordinates received");
            }

        } catch (Exception e) {
            log("Failed to parse JSON: " + e);
        }
    }

    public void updateObstacle(JSONObject target) {
        try {
            int obsID = Integer.parseInt(target.getString("obs_id"));
            int imgID = Integer.parseInt(target.getString("img_id"));
            map.setObsTargetID(obsID, imgID);
        } catch (Exception e) {
            log("Failed to parse JSON: " + e);
        }
    }

    public static void modifyObstacleVisibility(int position, boolean visible) {
        obsItems.setItemVisibility(position, visible);
        Log.d(TAG, "set obstacle "+position+" to "+visible);
    }

    public void log(String message) {
        Log.d(TAG, message);
    }

    // cancels the current toast and show the next one
    public void toast(String message) {
        if (currentToast != null) currentToast.cancel();
        currentToast = Toast.makeText(binding.getRoot().getContext(), message, Toast.LENGTH_SHORT);
        currentToast.show();
    }

}
