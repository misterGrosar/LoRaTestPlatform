package com.example.lora.loggpsposition;

import android.Manifest;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AlertDialog;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.TextView;

public class PermissionsActivity extends AppCompatActivity {
    private static final String TAG = "LogGPSPosition";
    private final int REQUEST_ALL_PREMISSIONS = 1;

    private TextView permissionTv;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        super.onCreate(savedInstanceState);
        setContentView(R.layout.permission_activity);

        permissionTv = (TextView) findViewById(R.id.permission);

        showPhonePermissions();
    }

    private void showPhonePermissions() {
        int permissionWLCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.WAKE_LOCK);
        int permissionICheck = ContextCompat.checkSelfPermission(this, Manifest.permission.INTERNET);
        int permissionNSCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_NETWORK_STATE);
        int permissionRPSCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE);
        int permissionFLCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION);
        int permissionCLCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION);

        if (permissionWLCheck != PackageManager.PERMISSION_GRANTED ||
                permissionICheck != PackageManager.PERMISSION_GRANTED ||
                permissionNSCheck != PackageManager.PERMISSION_GRANTED ||
                permissionRPSCheck != PackageManager.PERMISSION_GRANTED ||
                permissionFLCheck != PackageManager.PERMISSION_GRANTED ||
                permissionCLCheck != PackageManager.PERMISSION_GRANTED ) {
            String[] permissions = {
                    Manifest.permission.READ_PHONE_STATE,
                    Manifest.permission.INTERNET,
                    Manifest.permission.ACCESS_NETWORK_STATE,
                    Manifest.permission.READ_PHONE_STATE,
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION};

            if (ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.WAKE_LOCK) ||
                    ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.INTERNET) ||
                    ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.ACCESS_NETWORK_STATE) ||
                    ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.READ_PHONE_STATE) ||
                    ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.ACCESS_FINE_LOCATION) ||
                    ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.ACCESS_COARSE_LOCATION)) {
                showExplanation("Permission Needed", "Rationale", permissions, REQUEST_ALL_PREMISSIONS);
            } else {
                requestPermission(permissions, REQUEST_ALL_PREMISSIONS);
            }
        } else {
            permissionTv.setText("Permissions (already) Granted!");
            startMainActivity();
        }
    }

    private void showExplanation(String title, String message, final String[] permissions, final int permissionRequestCode) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(title)
                .setMessage(message)
                .setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int id) {
                        requestPermission(permissions, permissionRequestCode);
                    }
                });
        builder.create().show();
    }

    private void requestPermission(String[] permissionNames, int permissionRequestCode) {
        ActivityCompat.requestPermissions(this, permissionNames, permissionRequestCode);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String permissions[],int[] grantResults) {
        switch (requestCode) {
            case REQUEST_ALL_PREMISSIONS:
                if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    permissionTv.setText("Permissions Granted!");
                    startMainActivity();
                } else {
                    permissionTv.setText("Permissions Denied!");
                }
        }
    }

    private void startMainActivity(){
        Intent myIntent = new Intent(PermissionsActivity.this, MainActivity.class);
        myIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK |Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PermissionsActivity.this.startActivity(myIntent);
    }
}
