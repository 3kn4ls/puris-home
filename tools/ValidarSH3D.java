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
 *   java -Djava.awt.headless=true -cp SweetHome3D.jar tools/ValidarSH3D.java salida/casa_purisima.sh3d salida
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
      Dimension tamano = plano.getPreferredSize();
      plano.setSize(tamano);
      BufferedImage imagen = new BufferedImage(tamano.width, tamano.height, BufferedImage.TYPE_INT_RGB);
      Graphics2D g = imagen.createGraphics();
      g.setColor(Color.WHITE);
      g.fillRect(0, 0, tamano.width, tamano.height);
      plano.paint(g);
      g.dispose();
      File png = new File(carpeta, "plano_" + nivel.getName().toLowerCase().replace(' ', '_') + ".png");
      ImageIO.write(imagen, "png", png);
      System.out.println("  -> " + png);
    }
    System.exit(0);
  }
}
