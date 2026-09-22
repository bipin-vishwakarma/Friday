"""
Friday 2.0 Native APK Builder
Compiles and signs FridayHUD.apk using Android SDK build-tools and installs via ADB.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

SDK_DIR = Path(r"C:\Users\Lenovo\AppData\Local\Android\Sdk")
BUILD_TOOLS_DIR = SDK_DIR / "build-tools" / "33.0.2"
PLATFORM_JAR = SDK_DIR / "platforms" / "android-33-ext5" / "android.jar"

AAPT2 = str(BUILD_TOOLS_DIR / "aapt2.exe")
ZIPALIGN = str(BUILD_TOOLS_DIR / "zipalign.exe")
D8_JAR = str(BUILD_TOOLS_DIR / "lib" / "d8.jar")
APKSIGNER_JAR = str(BUILD_TOOLS_DIR / "lib" / "apksigner.jar")

WORK_DIR = Path(__file__).resolve().parent / "apk_build"

def run_cmd(cmd, check=True):
    print(f"[CMD] {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"[ERR] Command failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        raise RuntimeError(f"Build failed on: {cmd}")
    return res

def create_structure():
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    
    src_dir = WORK_DIR / "src" / "com" / "friday" / "hud"
    res_dir = WORK_DIR / "res" / "values"
    src_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    # 1. AndroidManifest.xml
    manifest_path = WORK_DIR / "AndroidManifest.xml"
    manifest_path.write_text("""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.friday.hud"
    android:versionCode="2"
    android:versionName="2.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />

    <application
        android:label="Friday HUD"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="sensor"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""")

    # 2. strings.xml
    (res_dir / "strings.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Friday HUD</string>
</resources>
""")

    # 3. MainActivity.java (uses top-level class AppClient to avoid Java 25 anonymous inner class metadata bug in D8)
    (src_dir / "MainActivity.java").write_text("""package com.friday.hud;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        setImmersive();

        webView = new WebView(this);
        setContentView(webView);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);

        webView.setWebViewClient(new AppClient());
        webView.loadUrl("http://localhost:5173");
    }

    private void setImmersive() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) setImmersive();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        }
    }
}

class AppClient extends WebViewClient {
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, String url) {
        view.loadUrl(url);
        return true;
    }
}
""")

def build():
    print("[*] Creating Android project files...")
    create_structure()

    compiled_res = WORK_DIR / "compiled_res"
    compiled_res.mkdir(exist_ok=True)

    # 1. Compile resources with AAPT2
    print("[*] Compiling resources with aapt2...")
    run_cmd(f'"{AAPT2}" compile --dir "{WORK_DIR / "res"}" -o "{compiled_res / "res.zip"}"')

    # 2. Link resources & generate R.java and initial APK
    print("[*] Linking with aapt2...")
    gen_dir = WORK_DIR / "gen"
    gen_dir.mkdir(exist_ok=True)
    unaligned_apk = WORK_DIR / "unaligned.apk"
    run_cmd(
        f'"{AAPT2}" link -I "{PLATFORM_JAR}" '
        f'--manifest "{WORK_DIR / "AndroidManifest.xml"}" '
        f'--java "{gen_dir}" '
        f'-o "{unaligned_apk}" '
        f'"{compiled_res / "res.zip"}"'
    )

    # 3. Compile Java classes
    print("[*] Compiling Java classes with javac...")
    classes_dir = WORK_DIR / "classes"
    classes_dir.mkdir(exist_ok=True)
    
    java_files = [
        str(WORK_DIR / "src" / "com" / "friday" / "hud" / "MainActivity.java"),
        str(gen_dir / "com" / "friday" / "hud" / "R.java")
    ]
    run_cmd(f'javac --release 8 -cp "{PLATFORM_JAR}" -d "{classes_dir}" ' + " ".join(f'"{f}"' for f in java_files))

    # 4. Dex classes with D8
    print("[*] Converting classes to DEX with D8...")
    class_files = []
    for root, _, files in os.walk(classes_dir):
        for f in files:
            if f.endswith(".class"):
                class_files.append(os.path.join(root, f))

    dex_dir = WORK_DIR / "dex"
    dex_dir.mkdir(exist_ok=True)
    run_cmd(f'java -cp "{D8_JAR}" com.android.tools.r8.D8 --min-api 26 --lib "{PLATFORM_JAR}" --output "{dex_dir}" ' + " ".join(f'"{f}"' for f in class_files))

    # 5. Add classes.dex into unaligned.apk
    print("[*] Packaging DEX into APK...")
    classes_dex = dex_dir / "classes.dex"
    with zipfile.ZipFile(unaligned_apk, 'a') as z:
        z.write(classes_dex, "classes.dex")

    # 6. Zipalign APK
    print("[*] Aligning APK with zipalign...")
    aligned_apk = WORK_DIR / "FridayHUD.apk"
    if aligned_apk.exists():
        aligned_apk.unlink()
    run_cmd(f'"{ZIPALIGN}" 4 "{unaligned_apk}" "{aligned_apk}"')

    # 7. Generate debug keystore if not exists
    keystore = WORK_DIR / "debug.keystore"
    if not keystore.exists():
        print("[*] Generating debug signing key...")
        run_cmd(f'keytool -genkeypair -v -keystore "{keystore}" -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"')

    # 8. Sign APK with apksigner
    print("[*] Signing APK with apksigner...")
    run_cmd(f'java -cp "{APKSIGNER_JAR}" com.android.apksigner.ApkSignerTool sign --ks "{keystore}" --ks-pass pass:android --ks-key-alias androiddebugkey --key-pass pass:android "{aligned_apk}"')

    output_dest = Path(__file__).resolve().parent.parent / "FridayHUD.apk"
    shutil.copyfile(aligned_apk, output_dest)
    print(f"\n[SUCCESS] Native Friday Android App built successfully: {output_dest}")
    return output_dest

if __name__ == "__main__":
    apk = build()
    # If device connected, install directly
    try:
        print("[*] Installing FridayHUD.apk to connected Samsung J2...")
        run_cmd(f'adb install -r "{apk}"')
        print("[*] Starting Friday HUD on phone...")
        run_cmd('adb shell am start -n com.friday.hud/.MainActivity')
        print("[OK] Friday HUD is running natively on Samsung J2!")
    except Exception as e:
        print(f"[INFO] APK ready. Could not auto-install: {e}")
