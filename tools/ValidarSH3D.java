import com.eteks.sweethome3d.io.DefaultUserPreferences;
import com.eteks.sweethome3d.io.HomeFileRecorder;
import com.eteks.sweethome3d.model.*;
import com.eteks.sweethome3d.swing.PlanComponent;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Locale;
import javax.imageio.ImageIO;

/**
 * Abre un .sh3d con el propio motor de Sweet Home 3D, lista lo que contiene
 * y dibuja el plano de cada planta en PNG.
 *
 * Uso (Java 11+, con SweetHome3D.jar descargado de sweethome3d.com):
 *   java -Djava.awt.headless=true -cp SweetHome3D.jar tools/ValidarSH3D.java salida/casa_purisima.sh3d salida [prefijo]
 * Con prefijo, los PNG se llaman <prefijo>_<nivel>.png, salen a más escala y
 * recortados al edificio (para comparar variantes).
 */
public class ValidarSH3D {
  public static void main(String[] args) throws Exception {
    Locale.setDefault(new Locale("es", "ES"));
    Home home = new HomeFileRecorder(0, false, null, false, true).readHome(args[0]);
    String carpeta = args.length > 1 ? args[1] : ".";
    Compass brujula = home.getCompass();
    System.out.printf("Brújula: norte %.1f°, lat %.5f, lon %.5f%n",
        Math.toDegrees(brujula.getNorthDirection()),
        Math.toDegrees(brujula.getLatitude()), Math.toDegrees(brujula.getLongitude()));
    UserPreferences preferencias = new DefaultUserPreferences();
    if (!GraphicsEnvironment.isHeadless()) {
      preferencias.setFurnitureViewedFromTop(true);  // muebles vistos desde arriba (necesita Java 3D)
    }
    for (Level nivel : home.getLevels()) {
      System.out.printf("%nNivel '%s': elevación %.0f cm, altura %.0f cm%n",
          nivel.getName(), nivel.getElevation(), nivel.getHeight());
      for (Wall muro : home.getWalls()) {
        if (muro.getLevel() == nivel) {
          System.out.printf("  Muro %.0f cm de largo, %.0f cm de grosor%n", muro.getLength(), muro.getThickness());
        }
      }
      for (HomePieceOfFurniture pieza : home.getFurniture()) {
        if (pieza.getLevel() == nivel) {
          System.out.printf("  Hueco '%s' %.0fx%.0f cm%n", pieza.getName(), pieza.getWidth(), pieza.getHeight());
        }
      }
      for (Room estancia : home.getRooms()) {
        if (estancia.getLevel() == nivel) {
          System.out.printf("  Estancia '%s' %.1f m²%n", estancia.getName(), estancia.getArea() / 10000);
        }
      }
      home.setSelectedLevel(nivel);
      PlanComponent plano = new PlanComponent(home, preferencias, null);
      String prefijo = args.length > 2 ? args[2] : null;
      if (prefijo != null) {
        plano.setScale(1.0f);
      }
      Dimension tamano = plano.getPreferredSize();
      plano.setSize(tamano);
      BufferedImage imagen = new BufferedImage(tamano.width, tamano.height, BufferedImage.TYPE_INT_RGB);
      plano.paint(imagen.createGraphics());  // primera pasada: lanza la carga de iconos
      Thread.sleep(1500);
      Graphics2D g = imagen.createGraphics();
      g.setColor(Color.WHITE);
      g.fillRect(0, 0, tamano.width, tamano.height);
      plano.paint(g);
      g.dispose();
      String sufijo = nivel.getName().toLowerCase().replace(' ', '_') + ".png";
      if (prefijo != null) {
        float minX = Float.MAX_VALUE, minY = Float.MAX_VALUE, maxX = -Float.MAX_VALUE, maxY = -Float.MAX_VALUE;
        for (Wall muro : home.getWalls()) {
          for (float[] p : muro.getPoints()) {
            minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]);
            minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]);
          }
        }
        int x0 = Math.max(0, plano.convertXModelToScreen(minX - 60));
        int y0 = Math.max(0, plano.convertYModelToScreen(minY - 60));
        int x1 = Math.min(tamano.width, plano.convertXModelToScreen(maxX + 60));
        int y1 = Math.min(tamano.height, plano.convertYModelToScreen(maxY + 60));
        imagen = imagen.getSubimage(x0, y0, x1 - x0, y1 - y0);
      }
      File png = new File(carpeta, (prefijo != null ? prefijo + "_" : "plano_") + sufijo);
      ImageIO.write(imagen, "png", png);
      System.out.println("  -> " + png);
    }
    System.exit(0);
  }
}
