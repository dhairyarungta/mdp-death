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
import com.example.mdp_android.databinding.FragmentHomeBinding;
import com.example.mdp_android.ui.grid.Map;

public class HomeFragment extends Fragment {
    private static final String TAG = "HomeFragment";
    private static final int SPAN = 2;
    private FragmentHomeBinding binding;
    private HomeViewModel homeViewModel;
    private String connectedDevice = "";

    public Map map;

    private ImageButton up, down, left, right;
    private Button resetBtn;
    private TextView robotStatus, targetCoor, bluetoothStatus, obsData;
    private RecyclerView obsList;
    private RecyclerAdapter obsItems;
    private RecyclerView.LayoutManager layoutManager;
    private TextView bluetoothTextView;
    private ToggleButton setRobot;


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

        return root;
    }

    // Update status whenever connection changes
    private BroadcastReceiver mNameReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String deviceName = intent.getStringExtra("name");
            if (deviceName.equals("")) {
                connectedDevice = "";
                homeViewModel.setReceivedText(context.getString(
                        R.string.bluetooth_device_connected_not));
            } else {
                connectedDevice = deviceName;
                Log.d(TAG, "onReceive: -msg- " + connectedDevice);
                homeViewModel.setReceivedText(context.getString(
                        R.string.bluetooth_device_connected)+connectedDevice);
            }
        }
    };


    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
        // below line causes broadcast to not be received
//        LocalBroadcastManager.getInstance(requireActivity()).unregisterReceiver(mNameReceiver);
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
        targetCoor = getView().findViewById(R.id.textView_targetCoor);
        obsData = getView().findViewById(R.id.textView_obsData);
        obsList = getView().findViewById(R.id.recyclerView_obsList);
        map = getView().findViewById(R.id.mapView);
        setRobot = getView().findViewById(R.id.button_startpoint);

        createObstacleList();

        resetBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                map.clearGrid();
                obsItems.setAllVisibility(true);
            }
        });

        up.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                log("move up");
            }
        });

        down.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                log("move down");
            }
        });

        left.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                log("move left");
            }
        });

        right.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                log("move right");
            }
        });

        setRobot.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
                String toast;
                if (b) {
                    toast = "Select a cell to place robot";
                } else {
                    toast = "Cancel";
                }
                Toast.makeText(getContext(), toast, Toast.LENGTH_LONG).show();
                map.setCanDrawRobot(b);
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
    }


    public void createObstacleList() {
        obsItems = new RecyclerAdapter(new String[]{"1", "2", "3", "4", "5", "6", "7", "8"});
        obsList.setAdapter(obsItems);
        layoutManager = new GridLayoutManager(getContext(), SPAN);
        obsList.setLayoutManager(layoutManager);

    }


    public void createObstacleDir() {

    }

    public void modifyObstacleVisibility(int position, boolean visible) {
        obsItems.setItemVisibility(position, visible);
        Log.d(TAG, "set obstacle "+position+" to "+visible);
    }

    public void log(String message) {
        Log.d(TAG, message);
    }


}
