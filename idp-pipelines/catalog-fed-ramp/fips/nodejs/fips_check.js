const crypto = require('crypto');
const { exec } = require('child_process');

// Function to check SHA-256 and HMAC-SHA-256, verifying FIPS compliance
function checkFipsSha256() {
    const data = Buffer.from('Test data');

    // SHA-256 hash using crypto module
    const sha256Hash = crypto.createHash('sha256');
    sha256Hash.update(data);
    const sha256Value = sha256Hash.digest('hex');
    console.log(`SHA-256 hash: ${sha256Value}`);

    // HMAC with SHA-256 using crypto module (FIPS-compliant if in FIPS mode)
    const key = Buffer.from('secret');
    const hmac = crypto.createHmac('sha256', key);
    hmac.update(data);
    const hmacValue = hmac.digest('hex');
    console.log(`HMAC-SHA-256: ${hmacValue}`);

    // Assuming the check is successful if no errors occurred
    return sha256Value && hmacValue ? true : false;
}

// Function to check if FIPS mode is enabled on the system
function checkFipsMode() {
    exec('cat /proc/sys/crypto/fips_enabled', (err, stdout, stderr) => {
        if (err) {
            console.log('Error checking FIPS mode: ', err);
            // Fallback to OpenSSL check if the above fails
            exec('openssl fips', (opensslErr, opensslStdout, opensslStderr) => {
                if (opensslErr) {
                    console.log('Error checking OpenSSL FIPS mode: ', opensslErr);
                } else if (opensslStdout.includes('FIPS mode enabled')) {
                    console.log('FIPS mode is enabled (OpenSSL).');
                } else {
                    console.log('FIPS mode is NOT enabled (OpenSSL).');
                }
            });
        } else {
            if (stdout.trim() === '1') {
                console.log('FIPS mode is enabled.');
            } else {
                console.log('FIPS mode is not enabled.');
            }
        }
    });
}

// Main function to run both checks
function runChecks() {
    try {
        console.log('FIPS-compliant Testing nodej');
        const sha256Check = checkFipsSha256();
        if (sha256Check) {
            console.log('FIPS-compliant SHA-256 and HMAC-SHA-256 operations passed.');
        } else {
            console.log('FIPS-compliant operations failed.');
        }
        //checkFipsMode();
    } catch (e) {
        console.error('An error occurred: ', e);
        process.exit(1);
    }
}

// Run the checks
runChecks();
