package com.example.mdp_android.ui.messages;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
public class MessagesViewModel extends ViewModel {
    private MutableLiveData<String> text;

    public MessagesViewModel() {
        text = new MutableLiveData<>();
        text.setValue("messages fragment");
    }

    public LiveData<String> getText() {
        return text;
    }
}
