// ============================================
// 🌍 Configuración global del proyecto Gradle
// ============================================

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.buildDir)
}
// ============================================
