package com.research.ccaf;

import android.os.Bundle;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;

import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.research.ccaf.ui.ChooseModelFragment;
import com.research.ccaf.ui.LiveRecordFragment;
import com.research.ccaf.ui.SelectFileFragment;

/**
 * Main Activity hosting the 3 core functional options:
 *  1. Live Record
 *  2. Select File
 *  3. Choose Model
 */
public class MainActivity extends AppCompatActivity {

    private final Fragment fragmentLiveRecord = new LiveRecordFragment();
    private final Fragment fragmentSelectFile = new SelectFileFragment();
    private final Fragment fragmentChooseModel = new ChooseModelFragment();
    private Fragment activeFragment = fragmentLiveRecord;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        FragmentManager fm = getSupportFragmentManager();
        fm.beginTransaction()
                .add(R.id.fragmentContainer, fragmentChooseModel, "3").hide(fragmentChooseModel)
                .add(R.id.fragmentContainer, fragmentSelectFile, "2").hide(fragmentSelectFile)
                .add(R.id.fragmentContainer, fragmentLiveRecord, "1")
                .commit();

        BottomNavigationView navView = findViewById(R.id.bottomNavigation);
        navView.setOnItemSelectedListener(item -> {
            int itemId = item.getItemId();
            if (itemId == R.id.nav_live_record) {
                fm.beginTransaction().hide(activeFragment).show(fragmentLiveRecord).commit();
                activeFragment = fragmentLiveRecord;
                return true;
            } else if (itemId == R.id.nav_select_file) {
                fm.beginTransaction().hide(activeFragment).show(fragmentSelectFile).commit();
                activeFragment = fragmentSelectFile;
                return true;
            } else if (itemId == R.id.nav_choose_model) {
                fm.beginTransaction().hide(activeFragment).show(fragmentChooseModel).commit();
                activeFragment = fragmentChooseModel;
                return true;
            }
            return false;
        });
    }
}
