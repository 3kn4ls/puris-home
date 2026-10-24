import com.eteks.sweethome3d.io.HomeFileRecorder;
import com.eteks.sweethome3d.j3d.PhotoRenderer;
import com.eteks.sweethome3d.model.*;

import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;

/**
 * Renderiza una vista 3D del .sh3d con el motor de fotos de Sweet Home 3D
 * (SunFlow), sin necesidad de pantalla ni OpenGL.
 *
 * Uso (con la carpeta lib/ de la versión de Sweet Home 3D para Linux o la portable):
 *   java -cp "lib/*" tools/Render3D.java salida/casa_purisima.sh3d salida/vista_3d.png [x y z yaw pitch [nivel]]
 * Sin cámara explícita usa la vista aérea guardada en el archivo. Si se indica
 * un nivel, se ocultan los que están por encima (para ver el interior).
 * Java 3D necesita una pantalla: en un servidor, lanzar con xvfb-run.
 */
public class Render3D {
  public static void main(String[] args) throws Exception {
    Home home = new HomeFileRecorder(0, false, null, false, true).readHome(args[0]);
    Camera camara = home.getTopCamera().clone();
    if (args.length >= 7) {
      camara.setX(Float.parseFloat(args[2]));
      camara.setY(Float.parseFloat(args[3]));
      camara.setZ(Float.parseFloat(args[4]));
      camara.setYaw(Float.parseFloat(args[5]));
      camara.setPitch(Float.parseFloat(args[6]));
    }
    if (args.length >= 8) {
      boolean ocultar = false;
      for (Level nivel : home.getLevels()) {
        nivel.setViewable(!ocultar);
        ocultar |= nivel.getName().equals(args[7]);
      }
    }
    BufferedImage imagen = new BufferedImage(1200, 800, BufferedImage.TYPE_INT_RGB);
    new PhotoRenderer(home, PhotoRenderer.Quality.LOW).render(imagen, camara, null);
    ImageIO.write(imagen, "png", new File(args[1]));
    System.out.println("-> " + args[1]);
    System.exit(0);
  }
}
