# ===============================================
# ✅ ProGuard rules para Flutter + Firebase
# ===============================================

# Mantener las clases de Flutter
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugins.** { *; }
-keep class io.flutter.embedding.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }

# ✅ CRÍTICO: Google Play Core (evita el error R8)
-keep class com.google.android.play.core.** { *; }
-dontwarn com.google.android.play.core.**
-keep class com.google.android.play.core.splitcompat.** { *; }
-keep class com.google.android.play.core.splitinstall.** { *; }
-keep class com.google.android.play.core.tasks.** { *; }

# Mantener las clases de Firebase
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.android.gms.**

# Mantener las clases de Geolocator y otros plugins
-keep class com.baseflow.** { *; }
-dontwarn com.baseflow.**

# Evitar eliminar clases usadas por reflexión
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes InnerClasses
-keepattributes EnclosingMethod

-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# Evitar eliminar modelos serializados
-keepclassmembers class * implements java.io.Serializable {
    static final long serialVersionUID;
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}

# ✅ Mantener clases de Kotlin
-keep class kotlin.** { *; }
-keep class kotlin.Metadata { *; }
-dontwarn kotlin.**
-keepclassmembers class **$WhenMappings {
    <fields>;
}
-keepclassmembers class kotlin.Metadata {
    public <methods>;
}

# ✅ Mantener clases de AndroidX
-keep class androidx.** { *; }
-keep interface androidx.** { *; }
-dontwarn androidx.**

# ✅ Optimizaciones seguras
-optimizations !code/simplification/arithmetic,!code/simplification/cast,!field/*,!class/merging/*
-optimizationpasses 5
-allowaccessmodification
-dontpreverify
