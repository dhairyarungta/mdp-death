package com.example.mdp_android.ui.messages;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.database.DataSetObserver;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ListView;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProvider;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import com.example.mdp_android.R;
import com.example.mdp_android.controllers.BluetoothController;
import com.example.mdp_android.controllers.BluetoothControllerSingleton;
import com.example.mdp_android.controllers.DeviceSingleton;
import com.example.mdp_android.databinding.FragmentMessagesBinding;

import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;

public class MessagesFragment extends Fragment {
    private static String TAG = "MessagesFragment";
    private FragmentMessagesBinding binding;
    private MessagesViewModel messagesViewModel;
    private Button sendBtn;
    private ImageButton clearReceivedBtn, clearSentBtn;
    private EditText eMessage;
    private ListView lvSentMessages;
    private ListView lvReceivedMessages;
    private static ArrayAdapter<String> aSentMessages;
    private static ArrayAdapter<String> aReceivedMessages;
    public static BluetoothController bController;

    DeviceSingleton deviceSingleton;

    @Override
    public View onCreateView(
            LayoutInflater inflater,
            ViewGroup container,
            Bundle savedInstanceState
    ) {
        messagesViewModel = new ViewModelProvider(this).get(MessagesViewModel.class);

        binding = FragmentMessagesBinding.inflate(inflater, container, false);
        View root = binding.getRoot();

        bController = BluetoothControllerSingleton.getInstance(new Handler());

        lvSentMessages = root.findViewById(R.id.listView_sent);

        lvReceivedMessages = root.findViewById(R.id.listview_received);

        eMessage = root.findViewById(R.id.editText_sendMessage);
        sendBtn = root.findViewById(R.id.button_send);
        clearReceivedBtn = root.findViewById(R.id.imageButton_clearReceived);
        clearSentBtn = root.findViewById(R.id.imageButton_clearSent);

        deviceSingleton = DeviceSingleton.getInstance();

        if (aSentMessages == null || aReceivedMessages == null) {
            aSentMessages = new ArrayAdapter<>(binding.getRoot().getContext(), R.layout.message_item);

            aReceivedMessages = new ArrayAdapter<>(binding.getRoot().getContext(), R.layout.message_item);
        }

        lvSentMessages.setAdapter(aSentMessages);
        aSentMessages.registerDataSetObserver(new DataSetObserver() {
            @Override
            public void onChanged() {
                super.onChanged();
                lvSentMessages.setSelection(aSentMessages.getCount() - 1);
            }
        });

        lvReceivedMessages.setAdapter(aReceivedMessages);
        aReceivedMessages.registerDataSetObserver(new DataSetObserver() {
            @Override
            public void onChanged() {
                super.onChanged();
                lvReceivedMessages.setSelection(lvSentMessages.getCount() - 1);
            }
        });

        // register receiver for receiving messages from connected device
        LocalBroadcastManager.getInstance(requireActivity()).registerReceiver(
                mTextReceiver,
                new IntentFilter("getReceived")
        );

        sendBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {

                String message = eMessage.getText().toString();
                if (deviceSingleton.getDeviceName().equals("")) {
                    toast("Bluetooth not connected to any device");
                } else if (message.equals("")) {
                    toast("Hey, don't just send empty strings");
                } else {
                    sendMessage(message);
                    toast("message sent: " + message);
                    eMessage.setText("");
                    appendASentMessages(message);
                }
            }
        });

        clearSentBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                aSentMessages.clear();
                toast("messages cleared");
            }
        });

        clearReceivedBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                aReceivedMessages.clear();
                toast("messages cleared");
            }
        });

        return root;
    }


    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        // remove receivers
        LocalBroadcastManager.getInstance(requireActivity()).unregisterReceiver(mTextReceiver);
    }

    private BroadcastReceiver mTextReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(TAG, "receiving messages");
            String textReceived = intent.getStringExtra("received");
            appendAReceivedMessages(textReceived);
        }
    };

    public static String getCurrentTime() {
        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");
        Date date = new Date();
        String dateStr = formatter.format(date).toString();
        return dateStr;
    }

    public static void appendASentMessages(String message) {
        aSentMessages.insert(getCurrentTime() + ": " + message, 0);
        aSentMessages.notifyDataSetChanged();
    }

    public static void appendAReceivedMessages(String message) {
        aReceivedMessages.insert(getCurrentTime() + ": " + message, 0);
        aReceivedMessages.notifyDataSetChanged();
    }

    private void sendMessage(String m) {
        bController.write(m.getBytes(StandardCharsets.UTF_8));
    }

    public void toast(String message) {
        Toast.makeText(getContext(), message, Toast.LENGTH_SHORT).show();
    }

}
