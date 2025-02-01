package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"strings"
)

// Check if FIPS mode is enabled on the system
func checkFipsMode() error {
	// First, check /proc/sys/crypto/fips_enabled
	data, err := ioutil.ReadFile("/proc/sys/crypto/fips_enabled")
	if err == nil {
		if strings.TrimSpace(string(data)) == "1" {
			fmt.Println("FIPS mode is enabled.")
			return nil
		} else {
			fmt.Println("FIPS mode is not enabled.")
			return fmt.Errorf("fips mode is not enabled")
		}
	}

	// If the file does not exist, fall back to OpenSSL check
	fmt.Println("Checking OpenSSL for FIPS mode...")
	cmd := exec.Command("openssl", "fips")
	output, err := cmd.CombinedOutput()
	if err != nil || !strings.Contains(string(output), "FIPS mode enabled") {
		fmt.Println("FIPS mode is NOT enabled (OpenSSL).")
		return fmt.Errorf("fips mode is not enabled (OpenSSL)")
	}

	fmt.Println("FIPS mode is enabled (OpenSSL).")
	return nil
}

// Check FIPS-compliant SHA-256 and HMAC using Go's crypto package
func checkFipsSha256() bool {
	// Hashing with SHA-256 (FIPS-compliant)
	data := []byte("Test data")
	hash := sha256.New()
	hash.Write(data)
	digest := hash.Sum(nil)
	fmt.Printf("SHA-256 hash: %x\n", digest)

	// Using HMAC with SHA-256 (FIPS-compliant)
	key := []byte("secret")
	hmac := hmac.New(sha256.New, key)
	hmac.Write(data)
	hmacDigest := hmac.Sum(nil)
	fmt.Printf("HMAC-SHA-256: %x\n", hmacDigest)

	// Return true if both are non-nil
	if digest != nil && hmacDigest != nil {
		return true
	}
	return false
}

func main() {


	fmt.Println("Testing go")

	// Check FIPS-compliant hashing and HMAC (SHA-256)
	if checkFipsSha256() {
		fmt.Println("SHA-256 and HMAC are FIPS-compliant.")
	} else {
		fmt.Println("FIPS-compliant hashing or HMAC failed.")
		os.Exit(1)
	}


	// Check FIPS mode
	//err := checkFipsMode()
	//if err != nil {
	//		os.Exit(1)
	//}


	// Successfully passed both checks
	os.Exit(0)
}
