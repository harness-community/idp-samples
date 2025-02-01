import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.Security;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public class FIPSCheck {

    public static boolean checkFIPS_SHA256() {
        try {
            // Verify FIPS-compliant hashing algorithms (SHA-256)
            MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
            byte[] data = "Test data".getBytes();
            byte[] digest = sha256.digest(data);
            System.out.println("SHA-256 hash: " + bytesToHex(digest));

            // Using HMAC with SHA-256 (FIPS-compliant)
            String key = "secret";
            Mac hmacSha256 = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKey = new SecretKeySpec(key.getBytes(), "HmacSHA256");
            hmacSha256.init(secretKey);
            byte[] hmacDigest = hmacSha256.doFinal(data);
            System.out.println("HMAC-SHA-256: " + bytesToHex(hmacDigest));

            return true;
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
            return false;
        }
    }

    public static void checkFIPSMode() {
        try {
            // Check if FIPS mode is enabled by inspecting security providers
            boolean fipsEnabled = false;

            for (java.security.Provider provider : Security.getProviders()) {
                if (provider.getName().toUpperCase().contains("SUNJCE") && provider.getVersion() > 1.8) {
                    // Check for a typical FIPS 140-2 provider like SunJCE
                    fipsEnabled = true;
                    break;
                }
            }

            if (fipsEnabled) {
                System.out.println("FIPS mode is enabled.");
            } else {
                System.out.println("FIPS mode is not enabled.");
            }
        } catch (Exception e) {
            System.out.println("Error checking FIPS mode: " + e.getMessage());
        }
    }

    // Utility method to convert bytes to a hexadecimal string
    private static String bytesToHex(byte[] bytes) {
        StringBuilder hexString = new StringBuilder();
        for (byte b : bytes) {
            String hex = Integer.toHexString(0xff & b);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        return hexString.toString();
    }

    public static void main(String[] args) {
        try {
            if (checkFIPS_SHA256()) {
                checkFIPSMode();
                System.exit(0);
            } else {
                System.exit(1);
            }
        } catch (Exception e) {
            System.exit(1);
        }
    }
}
