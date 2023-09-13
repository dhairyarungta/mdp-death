package com.example.mdp_android.ui.home;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import com.example.mdp_android.R;

public class HomeViewModel extends ViewModel {
    private MutableLiveData<String> mReceivedText;

    public HomeViewModel() {
        if (mReceivedText == null) {
            mReceivedText = new MutableLiveData<>();
            mReceivedText.setValue("Bluetooth: Not Connected");
        }
    }

    public LiveData<String> getReceivedText() {
        return mReceivedText;
    }

    public void setReceivedText(String text) { this.mReceivedText.setValue(text);}
}
