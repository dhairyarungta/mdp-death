package com.example.mdp_android.ui.bluetooth;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
public class BluetoothViewModel extends ViewModel{
    private MutableLiveData<String> device;

    public BluetoothViewModel() {
        device = new MutableLiveData<>();
        device.setValue("Bluetooth: Not Connected");
    }

    public LiveData<String> getDevice() {
        return device;
    }

    public void setDevice(String device) {
        this.device.setValue(device);
    }

}
