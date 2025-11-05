package com.deliber.app

import io.flutter.embedding.android.FlutterActivity
import android.os.Build
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Bundle

class MainActivity: FlutterActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Crear canal de notificaciones para Android 8.0+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channelId = "high_importance_channel"
            val channelName = "Notificaciones Importantes"
            val channelDescription = "Canal para notificaciones de alta prioridad"

            val channel = NotificationChannel(
                channelId,
                channelName,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = channelDescription
                enableVibration(true)
                enableLights(true)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager?.createNotificationChannel(channel)
        }
    }
}
