# Keep Molly classes
-keep class com.ariannamethod.molly.** { *; }

# Keep database models
-keepclassmembers class com.ariannamethod.molly.MollyDatabase$* {
    *;
}
