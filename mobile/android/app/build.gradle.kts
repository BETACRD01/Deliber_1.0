plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.gms.google-services")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.deliber.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.deliber.app"
        minSdk = flutter.minSdkVersion
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
        multiDexEnabled = true
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        // ✅ Necesario para Firebase Messaging y notificaciones
        isCoreLibraryDesugaringEnabled = true
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true // Limpia recursos no usados
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isDebuggable = true
            isMinifyEnabled = false
        }
    }

    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.2.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")

    // ✅ Desugaring para Java 8+ (necesario para notificaciones)
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.2")

    // 🔥 Firebase
    implementation(platform("com.google.firebase:firebase-bom:33.5.1"))
    implementation("com.google.firebase:firebase-messaging-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")

    // 🧩 Multidex
    implementation("androidx.multidex:multidex:2.0.1")

    // 🎮 Google Play Core (necesario para Flutter)
    implementation("com.google.android.play:core:1.10.3")
    implementation("com.google.android.play:core-ktx:1.8.1")
}

/* ✅ Copia automática del APK a la ruta por defecto de Flutter */
afterEvaluate {
    val assembleDebugTask = tasks.findByName("assembleDebug")
    val assembleReleaseTask = tasks.findByName("assembleRelease")
    val redirectTask = tasks.findByName("createDebugApkListingFileRedirect")

    listOfNotNull(assembleDebugTask, assembleReleaseTask).forEach { assembleTask ->
        val copyTask = tasks.register<Copy>("forceCopyApkToFlutterDefault_${assembleTask.name}") {
            dependsOn(assembleTask)

            // 📂 Ruta por defecto de Flutter
            val flutterProjectRoot = file("${rootProject.projectDir.parent}")
            val sourceApkDir = file("$buildDir/outputs/flutter-apk")
            val flutterDefaultDir = file("${flutterProjectRoot}/build/app/outputs/flutter-apk")

            from(sourceApkDir)
            include("*.apk")
            into(flutterDefaultDir)

            doFirst {
                println("📦 Copiando APK a ruta por defecto de Flutter:")
                println("   Origen: ${sourceApkDir.absolutePath}")
                println("   Destino: ${flutterDefaultDir.absolutePath}")
                flutterDefaultDir.mkdirs()
            }

            doLast {
                val apkFiles = flutterDefaultDir.listFiles { file -> file.extension == "apk" }
                if (apkFiles.isNullOrEmpty()) {
                    println("⚠️ Advertencia: No se encontraron archivos APK en el destino")
                } else {
                    println("✅ APK copiado correctamente:")
                    apkFiles.forEach { println("   • ${it.name} (${it.length() / 1024 / 1024} MB)") }
                }
            }
        }

        redirectTask?.mustRunAfter(copyTask)
        assembleTask.finalizedBy(copyTask)
    }
}
