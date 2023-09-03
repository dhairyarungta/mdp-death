package com.example.mdp_android.ui.home;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
public class HomeViewModel extends ViewModel {
    private MutableLiveData<String> text;

    public HomeViewModel() {
        text = new MutableLiveData<>();
        text.setValue("home");
    }

    public LiveData<String> getText() {
        return text;
    }
}
