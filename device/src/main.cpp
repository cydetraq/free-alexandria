#include <Arduino.h>
#include <DNSServer.h>
#include <ESPmDNS.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

#ifndef FREE_ALEXANDRIA_AP_SSID
#define FREE_ALEXANDRIA_AP_SSID "Free_Alexandria"
#endif

#ifndef FREE_ALEXANDRIA_HOSTNAME
#define FREE_ALEXANDRIA_HOSTNAME "free-alexandria"
#endif

#ifndef FREE_ALEXANDRIA_SD_CS
#define FREE_ALEXANDRIA_SD_CS 10
#endif

namespace {
constexpr uint16_t DNS_PORT = 53;
constexpr char INDEX_PATH[] = "/index.html";

DNSServer dnsServer;
AsyncWebServer server(80);
IPAddress apAddress(192, 168, 4, 1);

String contentTypeFor(const String &path) {
  if (path.endsWith(".html")) return "text/html; charset=utf-8";
  if (path.endsWith(".css")) return "text/css; charset=utf-8";
  if (path.endsWith(".js")) return "application/javascript; charset=utf-8";
  if (path.endsWith(".json")) return "application/json; charset=utf-8";
  if (path.endsWith(".epub")) return "application/epub+zip";
  if (path.endsWith(".pdf")) return "application/pdf";
  if (path.endsWith(".png")) return "image/png";
  if (path.endsWith(".jpg") || path.endsWith(".jpeg")) return "image/jpeg";
  if (path.endsWith(".webp")) return "image/webp";
  if (path.endsWith(".svg")) return "image/svg+xml";
  if (path.endsWith(".txt")) return "text/plain; charset=utf-8";
  return "application/octet-stream";
}

bool safePath(const String &path) {
  return path.startsWith("/") && path.indexOf("..") < 0 && path.indexOf('\\') < 0;
}

String normalizePath(AsyncWebServerRequest *request) {
  String path = request->url();
  const int query = path.indexOf('?');
  if (query >= 0) path = path.substring(0, query);
  if (path == "/") return INDEX_PATH;
  if (path.endsWith("/")) path += "index.html";
  return path;
}

void sendPortalRedirect(AsyncWebServerRequest *request) {
  AsyncWebServerResponse *response = request->beginResponse(302);
  response->addHeader("Location", String("http://") + apAddress.toString() + "/");
  response->addHeader("Cache-Control", "no-store");
  request->send(response);
}

void serveFromSd(AsyncWebServerRequest *request) {
  const String path = normalizePath(request);
  if (!safePath(path)) {
    request->send(400, "text/plain", "Invalid path");
    return;
  }

  if (!SD.exists(path)) {
    sendPortalRedirect(request);
    return;
  }

  AsyncWebServerResponse *response = request->beginResponse(
      SD, path, contentTypeFor(path), false);
  response->addHeader("Cache-Control", path.endsWith(".html") || path.endsWith(".json")
                                         ? "no-cache"
                                         : "public, max-age=86400");
  response->addHeader("X-Content-Type-Options", "nosniff");
  request->send(response);
}

void configureCaptivePortalRoutes() {
  // Common operating-system captive portal probes.
  server.on("/generate_204", HTTP_ANY, sendPortalRedirect);                // Android
  server.on("/gen_204", HTTP_ANY, sendPortalRedirect);                     // Android variants
  server.on("/hotspot-detect.html", HTTP_ANY, sendPortalRedirect);         // Apple
  server.on("/library/test/success.html", HTTP_ANY, sendPortalRedirect);    // Apple
  server.on("/connecttest.txt", HTTP_ANY, sendPortalRedirect);              // Windows
  server.on("/ncsi.txt", HTTP_ANY, sendPortalRedirect);                     // Windows
  server.on("/redirect", HTTP_ANY, sendPortalRedirect);                     // Firefox
  server.on("/canonical.html", HTTP_ANY, sendPortalRedirect);               // Firefox
  server.on("/success.txt", HTTP_ANY, sendPortalRedirect);                  // Firefox
  server.on("/fwlink", HTTP_ANY, sendPortalRedirect);                       // Windows

  server.onNotFound(serveFromSd);
}

void fatalBlink(const char *message) {
  Serial.println(message);
  pinMode(LED_BUILTIN, OUTPUT);
  while (true) {
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    delay(250);
  }
}
}  // namespace

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\nFree Alexandria captive portal starting");

  if (!SD.begin(FREE_ALEXANDRIA_SD_CS)) {
    fatalBlink("SD initialization failed. Check card format, wiring, and CS pin.");
  }
  if (!SD.exists(INDEX_PATH)) {
    fatalBlink("Missing /index.html on SD card. Copy a built Free Alexandria profile to the card root.");
  }

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(apAddress, apAddress, IPAddress(255, 255, 255, 0));
  if (!WiFi.softAP(FREE_ALEXANDRIA_AP_SSID)) {
    fatalBlink("Wi-Fi access point creation failed.");
  }

  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(DNS_PORT, "*", apAddress);

  if (MDNS.begin(FREE_ALEXANDRIA_HOSTNAME)) {
    MDNS.addService("http", "tcp", 80);
  }

  configureCaptivePortalRoutes();
  server.begin();

  Serial.printf("SSID: %s\n", FREE_ALEXANDRIA_AP_SSID);
  Serial.printf("Portal: http://%s/\n", apAddress.toString().c_str());
  Serial.printf("mDNS: http://%s.local/\n", FREE_ALEXANDRIA_HOSTNAME);
}

void loop() {
  dnsServer.processNextRequest();
  delay(2);
}
