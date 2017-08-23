package com.example.lora.loggpsposition;

import android.Manifest;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.PowerManager;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.res.ResourcesCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.text.DateFormat;
import java.text.MessageFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "LogGPSPosition";

    private String mServer = "tcp://<IP>:<port>"; // MQTTs server IP
    private String mTopicSub = "lora/test";
    private String mTopicPub = "lora/testGPSLog"; // MQTTs topic name
    private String mUsername = ""; // MQTTs username
    private String mPassword = ""; // MQTTs password
    private int mLogInterval = 1000; //GPS log interval in milliseconds

    private MqttAndroidClient mClient; // MQTT client
    private LocationManager mLocationManager;
    private LocationListener mLocationListener;
    private String mLogText;
    private boolean mPublishingGPS, mConnectedToMQTT;

    private TextView mLogConsoleTV;
    private Button mConnectBtn, mPublishBtn;
    private EditText mServerIpEt, mUsernemeEt, mPasswdEt, mTopicEt; //mLogIntervalEt;

    private PowerManager.WakeLock mWakeLock;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Lock screen orientation to portrait
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        super.onCreate(savedInstanceState);

        // Prevent screen from locking
        PowerManager mgr = (PowerManager)this.getSystemService(Context.POWER_SERVICE);
        mWakeLock = mgr.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "LogGPSPositionWakeLock");
        mWakeLock.acquire();

        setContentView(R.layout.main_activity);
        mLogText = "";
        mPublishingGPS = false;
        mConnectedToMQTT = false;
        
        mLogConsoleTV = (TextView) findViewById(R.id.loggerTxt);
        mLogConsoleTV.setMovementMethod(new ScrollingMovementMethod());

        mConnectBtn = (Button) findViewById(R.id.connectBtn);
        mPublishBtn = (Button) findViewById(R.id.publishBtn);

        mServerIpEt = ((EditText)findViewById(R.id.serverIpEt));
        mUsernemeEt = ((EditText)findViewById(R.id.usernameEt));
        mPasswdEt = ((EditText)findViewById(R.id.passwdEt));
        mTopicEt = ((EditText)findViewById(R.id.topicEt));
//        mLogIntervalEt = ((EditText)findViewById(R.id.logIntervalET));

        mServerIpEt.setText(mServer); // Pre fill input field
        mUsernemeEt.setText(mUsername); // Pre fill input field
        mPasswdEt.setText(mPassword); // Pre fill input field
        mTopicEt.setText(mTopicPub); // Pre fill input field
//        mLogIntervalEt.setText(mLogInterval + "");

        mPublishBtn.setEnabled(false); // Disable "Start" button when device is not connected to MQTT client

        mConnectBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View arg0) {
                if(mConnectedToMQTT) {
                    disconnectMqtt();// Disconnect from broker if device is already connected
                }
                else{
                    // Connect to MQTT broker
                    mServer = mServerIpEt.getText().toString();
                    mTopicPub = mTopicEt.getText().toString();
                    mUsername = mUsernemeEt.getText().toString();
                    mPassword = mPasswdEt.getText().toString();
                    connectoToMQTT();
                }
            }
        });

        mPublishBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View arg0) {
                if(!mPublishingGPS) {
                    logMessage("Starting logging location...");
//                    mLogInterval = Integer.parseInt(mLogIntervalEt.getText().toString());
                    runLocationManager(mLogInterval, 0);
                }
                else{
                    logMessage("Location logging stopped");
                    setBtnPublish(false);
                }
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();

    }

    /**
     * This method obtains GPS coordinates
     * @param updateTime
     * @param upgradeMeters
     */
    private void runLocationManager(int updateTime, int upgradeMeters) {
        mLocationManager = (LocationManager) this.getSystemService(Context.LOCATION_SERVICE);

        // Register the listener with the Location Manager to receive location updates
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED &&
                ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            // ActivityCompat#requestPermissions here to request the missing permissions, and then overriding
            // public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults)
            // to handle the case where the user grants the permission.
            logMessage("No location permission!");
            return;
        }
        logMessage("Obtaining GPS position...");
        logMessage("Locking on GPS...");
        mPublishBtn.setEnabled(true);
        setBtnPublish(true);

        mLocationListener = new MyLocationListener();
        mLocationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, updateTime, upgradeMeters, mLocationListener);
    }

    private class MyLocationListener implements LocationListener {
        @Override
        public void onLocationChanged(Location loc) {
            if(mPublishingGPS) {
                double longitude = loc.getLongitude();
                double latitude = loc.getLatitude();
                logMessage("Lon: " + longitude + ", lat: " + latitude);

                String toPublish = "{\"lon\":" + longitude + ",\"lat\":" + latitude +",\"time\":" + getCurrentMillis() + "}";
                publish(toPublish);
            }
        }

        @Override
        public void onProviderDisabled(String provider) {}

        @Override
        public void onProviderEnabled(String provider) {}

        @Override
        public void onStatusChanged(String provider, int status, Bundle extras) {}
    }

    /**
     * To get city name from coordinates
     * @param longitude
     * @param latitude
     * @return city name
     */
    private String getCity(double longitude, double latitude){
        Geocoder gcd = new Geocoder(getBaseContext(), Locale.getDefault());
        List<Address> addresses;
        try {
            addresses = gcd.getFromLocation(latitude, longitude, 1);
            if (addresses.size() > 0) {
                return addresses.get(0).getLocality();
            }
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        return "";
    }

    /**
     * Publish message to MQTT broker
     * @param payload
     */
    private void publish(String payload){
        byte[] encodedPayload = new byte[0];
        try {
            encodedPayload = payload.getBytes("UTF-8");
            MqttMessage message = new MqttMessage(encodedPayload);
            mClient.publish(mTopicPub, message);
        } catch (UnsupportedEncodingException | MqttException e) {
            e.printStackTrace();
        }
    }

    private void setBtnPublish(boolean publishing){
        if(publishing) {
            mPublishBtn.setText("Stop");
            mPublishBtn.setBackgroundColor(ResourcesCompat.getColor(getResources(), R.color.colorRed, null));
        }
        else{
            mPublishBtn.setText("Start");
            mPublishBtn.setBackgroundColor(ResourcesCompat.getColor(getResources(), R.color.colorPrimary, null));
        }
        mConnectBtn.setEnabled(!publishing);
//        mLogIntervalEt.setEnabled(!publishing);
        mPublishingGPS = publishing;
    }

    private void enableLoginInfoET(boolean enable){
        mServerIpEt.setEnabled(enable);
        mUsernemeEt.setEnabled(enable);
        mPasswdEt.setEnabled(enable);
        mTopicEt.setEnabled(enable);
    }

    /**
     * Show message in TextView
     * @param msg
     */
    private void logMessage(String msg){
        mLogText = "[" + getCurrnetTimeStamp() + "]:" + msg + "\n" + mLogText;
        mLogConsoleTV.setText(mLogText);
        Log.d(TAG, msg);
    }

    private void logErrorMessage(String msg){
        mLogText += "[" + getCurrnetTimeStamp() + "]:" + msg + "\n";
        mLogConsoleTV.setText(mLogText);
        Log.e(TAG, msg);
    }

    /**
     * Get current milliseconds
     * @return current milliseconds
     */
    private String getCurrentMillis(){
        Calendar rightNow = Calendar.getInstance();
        // offset to add since we're not UTC
        /*long offset = rightNow.get(Calendar.ZONE_OFFSET) + rightNow.get(Calendar.DST_OFFSET);
        long sinceMidnight = (rightNow.getTimeInMillis() + offset);*/
        long sinceMidnight = (rightNow.getTimeInMillis());
        return String.format ("%.3f", sinceMidnight / 1000.0);
    }

    /**
     * Get current timestamp
     * @return formatted timestamp
     */
    private String getCurrnetTimeStamp(){
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("GMT+2:00"));
        Date currentLocalTime = cal.getTime();
        DateFormat date = new SimpleDateFormat("HH:mm:ss");
        date.setTimeZone(TimeZone.getTimeZone("GMT+2:00"));

        return date.format(currentLocalTime);
    }

    /**
     * Connect to MQTT broker
     */
    private void connectoToMQTT(){
        logMessage("Connecting to MQTT...");
        mClient = new MqttAndroidClient(this.getApplicationContext(), mServer, "AndroidGPSLogger");

        try {
            MqttConnectOptions options = new MqttConnectOptions();
            options.setUserName(mUsername);
            options.setPassword(mPassword.toCharArray());

            IMqttToken token = mClient.connect(options);
            token.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    logMessage("Connected to " + mServer);
                    mConnectedToMQTT = true;

                    mConnectBtn.setText("Disconnect MQTT");
                    mPublishBtn.setEnabled(true);
                    mPublishBtn.setBackgroundColor(ResourcesCompat.getColor(getResources(), R.color.colorPrimary, null));
                    enableLoginInfoET(false);
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    // Something went wrong e.g. connection timeout or firewall problems
                    logErrorMessage("Error connecting to the " + mServer + ": " + exception.getMessage());

                }
            });
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void subscribeToMQTTTopic(){
        int qos = 1;
        try {
            IMqttToken subToken = mClient.subscribe(mTopicSub, qos);
            subToken.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    logMessage("Subscribed to " + mTopicSub);
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    // The subscription could not be performed, maybe the user was not
                    // authorized to subscribe on the specified topic e.g. using wildcards
                    logErrorMessage("ERROR subscribing to " + mTopicSub + ". " +exception.getMessage());
                }
            });
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void unsubscribeToMQTTTopic(){
        final String topic = "foo/bar";
        if(mClient != null) {
            try {
                IMqttToken unsubToken = mClient.unsubscribe(topic);
                unsubToken.setActionCallback(new IMqttActionListener() {
                    @Override
                    public void onSuccess(IMqttToken asyncActionToken) {
                        // The subscription could successfully be removed from the client
                        logMessage("MQTT client successfully unsubscribed from topic " + mTopicSub);
                    }

                    @Override
                    public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                        // some error occurred, this is very unlikely as even if the client
                        // did not had a subscription to the topic the unsubscribe action
                        // will be successfully
                        logErrorMessage("ERROR unsubscribing from topic " + mTopicSub);
                    }
                });
            } catch (MqttException e) {
                e.printStackTrace();
            }
        }
    }

    /**
     * Disconnect from MQTT broker
     */
    private void disconnectMqtt(){
        if(mClient != null) {
            try {
                IMqttToken disconToken = mClient.disconnect();
                disconToken.setActionCallback(new IMqttActionListener() {
                    @Override
                    public void onSuccess(IMqttToken asyncActionToken) {
                        mConnectBtn.setText("Connect MQTT");
                        mPublishBtn.setEnabled(false);
                        enableLoginInfoET(true);
                        logMessage("MQTT client successfully disconnected");
                        mConnectedToMQTT = false;
                    }

                    @Override
                    public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                        Log.e(TAG, "Error disconnecting MQTT client. " + exception.getMessage());
                    }
                });
            } catch (MqttException e) {
                Log.e(TAG, e.getMessage());
            }
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        mWakeLock.release();
        if (mLocationManager != null && mLocationListener != null) {
            mLocationManager.removeUpdates(mLocationListener);
        }
        if(mConnectedToMQTT) {
            disconnectMqtt();
        }
    }
}
