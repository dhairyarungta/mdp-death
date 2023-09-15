package com.example.mdp_android.ui.messages;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
public class MessagesViewModel extends ViewModel {
    private MutableLiveData<String> deviceName;

    public MessagesViewModel() {
        if (deviceName == null) {
            deviceName = new MutableLiveData<>();
            deviceName.setValue("Bluetooth: Not Connected");
        }
    }

    public LiveData<String> getDeviceName() { return deviceName; }
    public void setDeviceName(String text) { deviceName.setValue(text);}
}
