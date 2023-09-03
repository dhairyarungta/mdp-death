package com.example.mdp_android.ui.bluetooth;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
public class BluetoothViewModel extends ViewModel{
    private MutableLiveData<String> text;

    public BluetoothViewModel() {
        text = new MutableLiveData<>();
        text.setValue("bluetooth fragment");
    }

    public LiveData<String> getText() {
        return text;
    }
}
