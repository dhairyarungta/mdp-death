package com.example.mdp_android.ui.bluetooth;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

import com.example.mdp_android.databinding.FragmentBluetoothBinding;


public class BluetoothFragment extends Fragment {
    private BluetoothViewModel bluetoothViewModel;
    private FragmentBluetoothBinding binding;

    @Override
    public View onCreateView(
            LayoutInflater inflater,
            ViewGroup container,
            Bundle savedInstanceState
    ) {
        bluetoothViewModel = new ViewModelProvider(this).get(BluetoothViewModel.class);
        binding = FragmentBluetoothBinding.inflate(inflater, container, false);
        View root = binding.getRoot();

        return root;

    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

}
